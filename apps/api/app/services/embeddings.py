from collections.abc import Sequence

import cohere

from ..settings import settings

EMBEDDING_MODEL = "embed-multilingual-v3.0"
EMBEDDING_DIM = 1024
EMBEDDING_BATCH_SIZE = 96  # Cohere hard limit per request


class EmbeddingService:
    def __init__(self, client: cohere.AsyncClientV2 | None = None) -> None:
        if client is not None:
            self.client = client
        else:
            if not settings.cohere_api_key:
                raise RuntimeError("COHERE_API_KEY is not configured")
            self.client = cohere.AsyncClientV2(api_key=settings.cohere_api_key)

    async def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        cleaned = [text for text in texts if text.strip()]
        if len(cleaned) != len(texts):
            raise ValueError("Cannot embed empty chunk content")

        vectors: list[list[float]] = []
        for index in range(0, len(cleaned), EMBEDDING_BATCH_SIZE):
            batch = list(cleaned[index : index + EMBEDDING_BATCH_SIZE])
            response = await self.client.embed(
                texts=batch,
                model=EMBEDDING_MODEL,
                input_type="search_document",
                embedding_types=["float"],
            )
            if response.embeddings.float_ is None:
                raise RuntimeError("Cohere returned no float embeddings")
            vectors.extend(response.embeddings.float_)
        return vectors
