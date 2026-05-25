from types import SimpleNamespace
from typing import Any
import asyncio

from app.services.embeddings import EMBEDDING_BATCH_SIZE, EMBEDDING_MODEL, EmbeddingService


class FakeEmbeddingsClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[str]]] = []

    async def create(self, *, model: str, input: list[str]) -> Any:
        self.calls.append((model, input))
        data = [SimpleNamespace(index=index, embedding=[float(index)]) for index, _ in enumerate(input)]
        return SimpleNamespace(data=data)


class FakeOpenAIClient:
    def __init__(self) -> None:
        self.embeddings = FakeEmbeddingsClient()


def test_embedding_service_batches_in_groups_of_100() -> None:
    client = FakeOpenAIClient()
    service = EmbeddingService(client=client)  # type: ignore[arg-type]
    texts = [f"chunk {index}" for index in range(EMBEDDING_BATCH_SIZE * 2 + 5)]

    vectors = asyncio.run(service.embed_texts(texts))

    assert len(vectors) == len(texts)
    assert [len(call[1]) for call in client.embeddings.calls] == [100, 100, 5]
    assert all(call[0] == EMBEDDING_MODEL for call in client.embeddings.calls)
