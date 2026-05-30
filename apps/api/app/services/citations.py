import re
from dataclasses import dataclass

from .. import db
from .retrieve import RetrievedChunk

_WHITESPACE_RE = re.compile(r"\s+")
_SNIPPET_MAX = 200


@dataclass(frozen=True)
class Citation:
    index: int
    chunk_id: int
    material_id: str
    material_title: str
    page: int | None
    snippet: str


def _snippet(content: str) -> str:
    collapsed = _WHITESPACE_RE.sub(" ", content).strip()
    return collapsed[:_SNIPPET_MAX] + ("…" if len(collapsed) > _SNIPPET_MAX else "")


async def build_citations(chunks: list[RetrievedChunk]) -> list[Citation]:
    if not chunks:
        return []

    material_ids = list({c.material_id for c in chunks})
    connection = await db.connect()
    try:
        rows = await connection.fetch(
            """
            SELECT id::text, title FROM public.materials
            WHERE id = ANY($1::uuid[])
            """,
            material_ids,
        )
    finally:
        await connection.close()

    title_map: dict[str, str] = {str(row["id"]): str(row["title"]) for row in rows}

    return [
        Citation(
            index=i + 1,
            chunk_id=c.chunk_id,
            material_id=c.material_id,
            material_title=title_map.get(c.material_id, ""),
            page=c.page,
            snippet=_snippet(c.content),
        )
        for i, c in enumerate(chunks)
    ]


async def build_citations_for_chunk_ids(chunk_ids: list[int]) -> list[Citation]:
    """Resolve a list of chunk ids into ordered Citation objects.

    Used by the quiz results endpoint to turn a question's source_chunk_ids
    into citation chips. The index reflects the position in chunk_ids.
    """
    if not chunk_ids:
        return []

    connection = await db.connect()
    try:
        rows = await connection.fetch(
            """
            SELECT c.id, c.content, c.page, c.material_id::text AS material_id, m.title
            FROM public.chunks c
            JOIN public.materials m ON m.id = c.material_id
            WHERE c.id = ANY($1::bigint[])
            """,
            chunk_ids,
        )
    finally:
        await connection.close()

    by_id = {int(row["id"]): row for row in rows}

    citations: list[Citation] = []
    index = 1
    for chunk_id in chunk_ids:
        row = by_id.get(chunk_id)
        if row is None:
            continue
        citations.append(
            Citation(
                index=index,
                chunk_id=chunk_id,
                material_id=str(row["material_id"]),
                material_title=str(row["title"]),
                page=int(row["page"]) if row["page"] is not None else None,
                snippet=_snippet(str(row["content"])),
            )
        )
        index += 1
    return citations
