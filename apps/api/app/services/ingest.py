from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from io import BytesIO
from typing import Any

from docx import Document
from pypdf import PdfReader

from .. import db
from .chunker import HierarchicalChunker, ParentChunk, normalize_text
from .embeddings import EmbeddingService
from .storage import StorageService, get_storage_service

try:
    from langdetect import detect as langdetect_detect
except ModuleNotFoundError:  # pragma: no cover - dependency is installed in Phase 2 envs
    langdetect_detect = None


@dataclass(frozen=True)
class ParsedSegment:
    page: int | None
    text: str


@dataclass(frozen=True)
class ParsedMaterial:
    segments: list[ParsedSegment]
    page_count: int | None


async def ingest_uploaded_material(material_id: str, user_id: str) -> None:
    try:
        material = await _get_material(material_id, user_id)
        if material is None:
            return
        file_path = material.get("file_path")
        source_type = material.get("source_type")
        if not isinstance(file_path, str) or not isinstance(source_type, str):
            raise ValueError("Uploaded material is missing file metadata")

        raw = await get_storage_service().download_bytes(file_path)
        parsed = parse_uploaded_file(raw, source_type)
        await _ingest_segments(material_id, user_id, parsed)
    except Exception as exc:
        await _mark_failed(material_id, user_id, exc)


async def ingest_paste_material(material_id: str, user_id: str, content: str) -> None:
    try:
        parsed = ParsedMaterial(
            segments=[ParsedSegment(page=1, text=content)],
            page_count=1,
        )
        await _ingest_segments(material_id, user_id, parsed)
    except Exception as exc:
        await _mark_failed(material_id, user_id, exc)


def parse_uploaded_file(raw: bytes, source_type: str) -> ParsedMaterial:
    if source_type == "pdf":
        return _parse_pdf(raw)
    if source_type == "docx":
        return _parse_docx(raw)
    if source_type == "txt":
        return _parse_txt(raw)
    raise ValueError(f"Unsupported source type: {source_type}")


def _parse_pdf(raw: bytes) -> ParsedMaterial:
    reader = PdfReader(BytesIO(raw))
    segments: list[ParsedSegment] = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            segments.append(ParsedSegment(page=index, text=text))
    return ParsedMaterial(segments=segments, page_count=len(reader.pages))


def _parse_docx(raw: bytes) -> ParsedMaterial:
    document = Document(BytesIO(raw))
    paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
    return ParsedMaterial(
        segments=[ParsedSegment(page=1, text="\n".join(paragraphs))],
        page_count=1,
    )


def _parse_txt(raw: bytes) -> ParsedMaterial:
    for encoding in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = raw.decode("utf-8", errors="replace")
    return ParsedMaterial(segments=[ParsedSegment(page=1, text=text)], page_count=1)


async def _ingest_segments(material_id: str, user_id: str, parsed: ParsedMaterial) -> None:
    pages = [(segment.page, segment.text) for segment in parsed.segments if segment.text.strip()]
    combined_text = "\n".join(text for _, text in pages)
    if not normalize_text(combined_text):
        raise ValueError("No extractable text found")

    lang = detect_language(combined_text)
    parents = HierarchicalChunker().split_document(pages)
    if not parents:
        raise ValueError("No chunks produced from material")

    child_texts = [child.content for parent in parents for child in parent.children]
    embeddings = await EmbeddingService().embed_texts(child_texts)
    if len(embeddings) != len(child_texts):
        raise RuntimeError("Embedding count did not match chunk count")

    await _save_chunks(material_id, user_id, parsed.page_count, lang, parents, embeddings)


def detect_language(text: str) -> str:
    sample = normalize_text(text)[:5000]
    if len(sample) < 20 or langdetect_detect is None:
        return "unknown"
    try:
        return str(langdetect_detect(sample))
    except Exception:
        return "unknown"


async def _get_material(material_id: str, user_id: str) -> dict[str, Any] | None:
    connection = await db.connect()
    try:
        row = await connection.fetchrow(
            """
            select id, source_type, file_path
            from public.materials
            where id = $1::uuid and user_id = $2::uuid
            """,
            material_id,
            user_id,
        )
        return dict(row) if row else None
    finally:
        await connection.close()


async def _save_chunks(
    material_id: str,
    user_id: str,
    page_count: int | None,
    lang: str,
    parents: Sequence[ParentChunk],
    embeddings: Sequence[Sequence[float]],
) -> None:
    connection = await db.connect()
    child_embedding_index = 0
    chunk_ord = 0
    try:
        async with connection.transaction():
            await connection.execute(
                "delete from public.chunks where material_id = $1::uuid and user_id = $2::uuid",
                material_id,
                user_id,
            )
            await connection.execute(
                """
                update public.materials
                set page_count = $1,
                    lang_detected = $2,
                    status = 'processing',
                    error_message = null
                where id = $3::uuid and user_id = $4::uuid
                """,
                page_count,
                lang,
                material_id,
                user_id,
            )

            for parent in parents:
                chunk_ord += 1
                parent_id = await connection.fetchval(
                    """
                    insert into public.chunks
                      (user_id, material_id, content, page, ord, chunk_level, parent_chunk_id, embedding)
                    values ($1::uuid, $2::uuid, $3, $4, $5, 'parent', null, null)
                    returning id
                    """,
                    user_id,
                    material_id,
                    parent.content,
                    parent.page,
                    chunk_ord,
                )
                for child in parent.children:
                    embedding = embeddings[child_embedding_index]
                    child_embedding_index += 1
                    chunk_ord += 1
                    await connection.execute(
                        """
                        insert into public.chunks
                          (user_id, material_id, content, page, ord, chunk_level, parent_chunk_id, embedding)
                        values ($1::uuid, $2::uuid, $3, $4, $5, 'child', $6, $7::vector)
                        """,
                        user_id,
                        material_id,
                        child.content,
                        child.page,
                        chunk_ord,
                        parent_id,
                        vector_literal(embedding),
                    )

            await connection.execute(
                """
                update public.materials
                set status = 'ready',
                    error_message = null
                where id = $1::uuid and user_id = $2::uuid
                """,
                material_id,
                user_id,
            )
    finally:
        await connection.close()


def vector_literal(values: Iterable[float]) -> str:
    return "[" + ",".join(f"{float(value):.8g}" for value in values) + "]"


async def _mark_failed(material_id: str, user_id: str, exc: Exception) -> None:
    message = str(exc).strip() or exc.__class__.__name__
    connection = await db.connect()
    try:
        await connection.execute(
            """
            update public.materials
            set status = 'failed',
                error_message = $1
            where id = $2::uuid and user_id = $3::uuid
            """,
            message[:500],
            material_id,
            user_id,
        )
    finally:
        await connection.close()
