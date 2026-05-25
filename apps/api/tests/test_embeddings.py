from types import SimpleNamespace
from typing import Any
import asyncio

from app.services.embeddings import EMBEDDING_BATCH_SIZE, EMBEDDING_MODEL, EmbeddingService


class FakeCohereClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[str], str]] = []

    async def embed(self, *, texts: list[str], model: str, input_type: str, embedding_types: list[str]) -> Any:
        self.calls.append((model, texts, input_type))
        return SimpleNamespace(
            embeddings=SimpleNamespace(float_=[[float(i)] for i in range(len(texts))])
        )


def test_embedding_service_batches_in_groups_of_96() -> None:
    client = FakeCohereClient()
    service = EmbeddingService(client=client)  # type: ignore[arg-type]
    texts = [f"chunk {index}" for index in range(EMBEDDING_BATCH_SIZE * 2 + 5)]

    vectors = asyncio.run(service.embed_texts(texts))

    assert len(vectors) == len(texts)
    assert [len(call[1]) for call in client.calls] == [96, 96, 5]
    assert all(call[0] == EMBEDDING_MODEL for call in client.calls)
