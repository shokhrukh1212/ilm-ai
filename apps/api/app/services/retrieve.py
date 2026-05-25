import logging
from dataclasses import dataclass

import cohere

from .. import db
from ..settings import settings
from .embeddings import EmbeddingService

logger = logging.getLogger(__name__)

_RRF_SQL = """
WITH vec AS (
  SELECT id, ROW_NUMBER() OVER (ORDER BY embedding <=> $1::vector) AS r
  FROM public.chunks
  WHERE material_id = ANY($2::uuid[])
    AND user_id = $3::uuid
    AND chunk_level = 'child'
    AND embedding IS NOT NULL
  LIMIT 30
),
bm AS (
  SELECT id, ROW_NUMBER() OVER (ORDER BY ts_rank_cd(tsv, plainto_tsquery('simple', $4)) DESC) AS r
  FROM public.chunks
  WHERE material_id = ANY($2::uuid[])
    AND user_id = $3::uuid
    AND chunk_level = 'child'
    AND tsv @@ plainto_tsquery('simple', $4)
  LIMIT 30
)
SELECT c.id, c.content, c.page, c.material_id::text,
       COALESCE(1.0 / (60 + v.r), 0) + COALESCE(1.0 / (60 + b.r), 0) AS score
FROM vec v
FULL OUTER JOIN bm b USING (id)
JOIN public.chunks c ON c.id = COALESCE(v.id, b.id)
ORDER BY score DESC
LIMIT 20
"""


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: int
    content: str
    page: int | None
    material_id: str
    score: float


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{v:.8g}" for v in values) + "]"


async def retrieve(
    query: str,
    material_ids: list[str],
    user_id: str,
    top_k: int = 5,
) -> list[RetrievedChunk]:
    embedding_service = EmbeddingService()
    query_vector = await embedding_service.embed_query(query)
    vector_str = _vector_literal(query_vector)

    connection = await db.connect()
    try:
        rows = await connection.fetch(
            _RRF_SQL,
            vector_str,
            material_ids,
            user_id,
            query,
        )
    finally:
        await connection.close()

    candidates = [
        RetrievedChunk(
            chunk_id=int(row["id"]),
            content=str(row["content"]),
            page=int(row["page"]) if row["page"] is not None else None,
            material_id=str(row["material_id"]),
            score=float(row["score"]),
        )
        for row in rows
    ]

    if not candidates:
        return []

    return await _rerank(query, candidates, top_k)


async def _rerank(
    query: str,
    candidates: list[RetrievedChunk],
    top_k: int,
) -> list[RetrievedChunk]:
    if not settings.cohere_api_key:
        logger.warning("COHERE_API_KEY not set; skipping rerank, using RRF top-%d", top_k)
        return candidates[:top_k]

    try:
        client = cohere.AsyncClientV2(api_key=settings.cohere_api_key)
        result = await client.rerank(
            model="rerank-v3.5",
            query=query,
            documents=[c.content for c in candidates],
            top_n=top_k,
        )
        return [candidates[r.index] for r in result.results]
    except Exception:
        logger.warning("Cohere rerank failed; falling back to RRF top-%d", top_k, exc_info=True)
        return candidates[:top_k]
