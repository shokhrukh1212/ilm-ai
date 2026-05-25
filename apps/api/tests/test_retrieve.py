import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.retrieve import RetrievedChunk, _rerank, retrieve


class FakeEmbeddingService:
    async def embed_query(self, text: str) -> list[float]:
        return [0.1] * 1024


class FakeRerankResult:
    def __init__(self, index: int) -> None:
        self.index = index


class FakeRerankResponse:
    def __init__(self, indices: list[int]) -> None:
        self.results = [FakeRerankResult(i) for i in indices]


def _chunk(chunk_id: int) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        content=f"Content for chunk {chunk_id}",
        page=chunk_id,
        material_id="mat-1",
        score=1.0 / chunk_id,
    )


class TestRerank:
    def test_falls_back_to_rrf_when_cohere_key_missing(self) -> None:
        candidates = [_chunk(i) for i in range(1, 10)]
        with patch("app.services.retrieve.settings") as mock_settings:
            mock_settings.cohere_api_key = ""
            result = asyncio.run(_rerank("query", candidates, 5))
        assert result == candidates[:5]

    def test_reorders_by_cohere_ranking(self) -> None:
        candidates = [_chunk(i) for i in range(1, 6)]
        fake_response = FakeRerankResponse([4, 3, 2, 1, 0])

        async def fake_rerank(**_kwargs: Any) -> FakeRerankResponse:
            return fake_response

        fake_client = MagicMock()
        fake_client.rerank = fake_rerank

        with patch("app.services.retrieve.settings") as mock_settings, \
             patch("app.services.retrieve.cohere") as mock_cohere:
            mock_settings.cohere_api_key = "test-key"
            mock_cohere.AsyncClientV2.return_value = fake_client
            result = asyncio.run(_rerank("query", candidates, 5))

        assert result == [candidates[4], candidates[3], candidates[2], candidates[1], candidates[0]]

    def test_falls_back_to_rrf_on_cohere_error(self) -> None:
        candidates = [_chunk(i) for i in range(1, 10)]

        async def failing_rerank(**_kwargs: Any) -> FakeRerankResponse:
            raise RuntimeError("network error")

        fake_client = MagicMock()
        fake_client.rerank = failing_rerank

        with patch("app.services.retrieve.settings") as mock_settings, \
             patch("app.services.retrieve.cohere") as mock_cohere:
            mock_settings.cohere_api_key = "test-key"
            mock_cohere.AsyncClientV2.return_value = fake_client
            result = asyncio.run(_rerank("query", candidates, 5))

        assert result == candidates[:5]

    def test_returns_top_k(self) -> None:
        candidates = [_chunk(i) for i in range(1, 21)]
        with patch("app.services.retrieve.settings") as mock_settings:
            mock_settings.cohere_api_key = ""
            result = asyncio.run(_rerank("query", candidates, 3))
        assert len(result) == 3
