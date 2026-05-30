import math

from .. import db
from .retrieve import RetrievedChunk

# Cap on how many child chunks we feed the quiz generator. Keeps the prompt
# within a sane token budget (~300 tokens/chunk) so generation stays well
# under the 15s acceptance budget.
DEFAULT_MAX_CHUNKS = 40


async def fetch_quiz_sources(
    material_id: str,
    user_id: str,
    max_chunks: int = DEFAULT_MAX_CHUNKS,
) -> list[RetrievedChunk]:
    """Fetch child chunks for a material, evenly sampled across the whole text.

    The quiz generator has no search query, so we sample chunks spread across
    the material (by stored order) rather than only the opening section. This
    gives questions broad coverage of the full material.
    """
    connection = await db.connect()
    try:
        rows = await connection.fetch(
            """
            SELECT id, content, page, material_id::text, ord
            FROM public.chunks
            WHERE material_id = $1::uuid
              AND user_id = $2::uuid
              AND chunk_level = 'child'
            ORDER BY ord ASC
            """,
            material_id,
            user_id,
        )
    finally:
        await connection.close()

    chunks = [
        RetrievedChunk(
            chunk_id=int(row["id"]),
            content=str(row["content"]),
            page=int(row["page"]) if row["page"] is not None else None,
            material_id=str(row["material_id"]),
            score=0.0,
        )
        for row in rows
    ]

    return _even_sample(chunks, max_chunks)


def _even_sample(chunks: list[RetrievedChunk], max_chunks: int) -> list[RetrievedChunk]:
    if max_chunks <= 0 or len(chunks) <= max_chunks:
        return chunks
    stride = math.ceil(len(chunks) / max_chunks)
    return chunks[::stride][:max_chunks]


def build_sources_block(chunks: list[RetrievedChunk]) -> str:
    """Render chunks labeled by their real chunks.id.

    Questions reference these ids in source_chunk_ids, which lets the results
    page resolve them back to real rows for citations.
    """
    lines = [
        f"[chunk {c.chunk_id}] (p.{c.page}) {c.content}"
        if c.page is not None
        else f"[chunk {c.chunk_id}] {c.content}"
        for c in chunks
    ]
    return "\n".join(lines)
