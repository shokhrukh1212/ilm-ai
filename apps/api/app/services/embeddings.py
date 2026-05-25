from collections.abc import Sequence

from openai import AsyncOpenAI

from ..settings import settings

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_BATCH_SIZE = 100


class EmbeddingService:
    def __init__(self, client: AsyncOpenAI | None = None) -> None:
        if client is not None:
            self.client = client
        else:
            if not settings.openai_api_key:
                raise RuntimeError("OPENAI_API_KEY is not configured")
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        cleaned = [text for text in texts if text.strip()]
        if len(cleaned) != len(texts):
            raise ValueError("Cannot embed empty chunk content")

        vectors: list[list[float]] = []
        for index in range(0, len(cleaned), EMBEDDING_BATCH_SIZE):
            batch = cleaned[index : index + EMBEDDING_BATCH_SIZE]
            response = await self.client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=list(batch),
            )
            vectors.extend([item.embedding for item in sorted(response.data, key=lambda item: item.index)])
        return vectors
