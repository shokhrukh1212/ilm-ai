from datetime import datetime
from pathlib import Path
import re
from typing import Annotated, Literal, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Response, UploadFile, status
from pydantic import BaseModel, Field

from .. import db
from ..auth import get_current_user_id
from ..services.ingest import ingest_paste_material, ingest_uploaded_material
from ..services.storage import get_storage_service

router = APIRouter(prefix="/api/v1/materials", tags=["materials"])

MAX_UPLOAD_BYTES = 50 * 1024 * 1024
MAX_PASTE_CHARS = 100_000

SourceType = Literal["pdf", "docx", "txt", "paste"]
MaterialStatus = Literal["processing", "ready", "failed"]

MIME_BY_SOURCE: dict[str, str] = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "txt": "text/plain",
}

EXTENSION_TO_SOURCE: dict[str, SourceType] = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".txt": "txt",
}


class MaterialResponse(BaseModel):
    id: UUID
    title: str
    source_type: SourceType
    file_name: str | None = None
    file_path: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = None
    page_count: int | None = None
    lang_detected: str | None = None
    status: MaterialStatus
    error_message: str | None = None
    chunks_count: int = 0
    signed_url: str | None = None
    created_at: datetime
    updated_at: datetime


class UploadUrlRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=240)
    content_type: str = Field(min_length=1, max_length=160)
    size_bytes: int = Field(ge=1, le=MAX_UPLOAD_BYTES)


class UploadUrlResponse(BaseModel):
    material_id: UUID
    bucket: str
    path: str
    token: str
    signed_url: str
    status: MaterialStatus


class PasteRequest(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    content: str = Field(min_length=1, max_length=MAX_PASTE_CHARS)


@router.get("", response_model=list[MaterialResponse])
async def list_materials(user_id: Annotated[str, Depends(get_current_user_id)]) -> list[MaterialResponse]:
    connection = await db.connect()
    try:
        rows = await connection.fetch(
            """
            select
              m.*,
              coalesce(count(c.id) filter (where c.chunk_level = 'child'), 0)::int as chunks_count
            from public.materials m
            left join public.chunks c
              on c.material_id = m.id
             and c.user_id = m.user_id
            where m.user_id = $1::uuid
            group by m.id
            order by m.created_at desc
            """,
            user_id,
        )
        return [_material_response(dict(row)) for row in rows]
    finally:
        await connection.close()


@router.get("/{material_id}", response_model=MaterialResponse)
async def get_material(
    material_id: UUID,
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> MaterialResponse:
    row = await _get_material_row(str(material_id), user_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")

    signed_url: str | None = None
    file_path = row.get("file_path")
    if isinstance(file_path, str):
        try:
            signed_url = await get_storage_service().create_signed_read_url(file_path)
        except Exception:
            signed_url = None
    return _material_response(row, signed_url=signed_url)


@router.post("/upload", response_model=MaterialResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_material(
    background_tasks: BackgroundTasks,
    user_id: Annotated[str, Depends(get_current_user_id)],
    file: UploadFile = File(...),
) -> MaterialResponse:
    safe_name, source_type, content_type = _validate_file_metadata(file.filename or "", file.content_type)
    raw = await _read_upload_file(file)
    material_id = uuid4()
    storage_path = _storage_path(user_id, material_id, safe_name)

    await get_storage_service().upload_bytes(storage_path, raw, content_type)
    row = await _insert_material(
        material_id=material_id,
        user_id=user_id,
        title=_title_from_filename(file.filename or safe_name),
        source_type=source_type,
        file_name=safe_name,
        file_path=storage_path,
        mime_type=content_type,
        size_bytes=len(raw),
    )
    background_tasks.add_task(ingest_uploaded_material, str(material_id), user_id)
    return _material_response(row)


@router.post("/upload-url", response_model=UploadUrlResponse, status_code=status.HTTP_201_CREATED)
async def create_upload_url(
    body: UploadUrlRequest,
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> UploadUrlResponse:
    safe_name, source_type, content_type = _validate_file_metadata(body.filename, body.content_type)
    material_id = uuid4()
    storage_path = _storage_path(user_id, material_id, safe_name)
    signed = await get_storage_service().create_signed_upload_url(storage_path)

    await _insert_material(
        material_id=material_id,
        user_id=user_id,
        title=_title_from_filename(body.filename),
        source_type=source_type,
        file_name=safe_name,
        file_path=storage_path,
        mime_type=content_type,
        size_bytes=body.size_bytes,
    )
    return UploadUrlResponse(
        material_id=material_id,
        bucket=get_storage_service().bucket,
        path=storage_path,
        token=signed["token"],
        signed_url=signed["signed_url"],
        status="processing",
    )


@router.post("/{material_id}/upload-complete", response_model=MaterialResponse, status_code=status.HTTP_202_ACCEPTED)
async def complete_signed_upload(
    material_id: UUID,
    background_tasks: BackgroundTasks,
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> MaterialResponse:
    row = await _get_material_row(str(material_id), user_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")
    if row.get("source_type") == "paste" or not row.get("file_path"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Material has no uploaded file")

    await _set_processing(str(material_id), user_id)
    background_tasks.add_task(ingest_uploaded_material, str(material_id), user_id)
    updated = await _get_material_row(str(material_id), user_id)
    return _material_response(updated or row)


@router.post("/paste", response_model=MaterialResponse, status_code=status.HTTP_202_ACCEPTED)
async def paste_material(
    body: PasteRequest,
    background_tasks: BackgroundTasks,
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> MaterialResponse:
    material_id = uuid4()
    row = await _insert_material(
        material_id=material_id,
        user_id=user_id,
        title=body.title.strip(),
        source_type="paste",
        file_name=None,
        file_path=None,
        mime_type="text/plain",
        size_bytes=len(body.content.encode("utf-8")),
    )
    background_tasks.add_task(ingest_paste_material, str(material_id), user_id, body.content)
    return _material_response(row)


@router.delete("/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_material(
    material_id: UUID,
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> Response:
    row = await _get_material_row(str(material_id), user_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")

    file_path = row.get("file_path")
    if isinstance(file_path, str):
        try:
            await get_storage_service().remove(file_path)
        except Exception:
            pass

    connection = await db.connect()
    try:
        await connection.execute(
            "delete from public.materials where id = $1::uuid and user_id = $2::uuid",
            str(material_id),
            user_id,
        )
    finally:
        await connection.close()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def _read_upload_file(file: UploadFile) -> bytes:
    raw = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File is over 50MB")
    if not raw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty")
    return raw


def _validate_file_metadata(filename: str, content_type: str | None) -> tuple[str, SourceType, str]:
    suffix = Path(filename).suffix.lower()
    source_type = EXTENSION_TO_SOURCE.get(suffix)
    if source_type is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF, DOCX, and TXT are supported")

    safe_name = _safe_filename(filename)
    return safe_name, source_type, MIME_BY_SOURCE[source_type]


def _safe_filename(filename: str) -> str:
    basename = Path(filename).name.strip()
    if not basename:
        basename = "material.txt"
    suffix = Path(basename).suffix.lower()
    stem = Path(basename).stem or "material"
    safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._-") or "material"
    return f"{safe_stem[:150]}{suffix}"


def _title_from_filename(filename: str) -> str:
    stem = Path(filename).stem.strip()
    return stem[:180] or "Material"


def _storage_path(user_id: str, material_id: UUID, filename: str) -> str:
    return f"{user_id}/{material_id}/{filename}"


async def _insert_material(
    *,
    material_id: UUID,
    user_id: str,
    title: str,
    source_type: SourceType,
    file_name: str | None,
    file_path: str | None,
    mime_type: str | None,
    size_bytes: int | None,
) -> dict[str, object]:
    connection = await db.connect()
    try:
        row = await connection.fetchrow(
            """
            insert into public.materials
              (id, user_id, title, source_type, file_name, file_path, mime_type, size_bytes, status)
            values ($1::uuid, $2::uuid, $3, $4, $5, $6, $7, $8, 'processing')
            returning *
            """,
            str(material_id),
            user_id,
            title,
            source_type,
            file_name,
            file_path,
            mime_type,
            size_bytes,
        )
        return dict(row)
    finally:
        await connection.close()


async def _get_material_row(material_id: str, user_id: str) -> dict[str, object] | None:
    connection = await db.connect()
    try:
        row = await connection.fetchrow(
            """
            select
              m.*,
              coalesce(count(c.id) filter (where c.chunk_level = 'child'), 0)::int as chunks_count
            from public.materials m
            left join public.chunks c
              on c.material_id = m.id
             and c.user_id = m.user_id
            where m.id = $1::uuid and m.user_id = $2::uuid
            group by m.id
            """,
            material_id,
            user_id,
        )
        return dict(row) if row else None
    finally:
        await connection.close()


async def _set_processing(material_id: str, user_id: str) -> None:
    connection = await db.connect()
    try:
        await connection.execute(
            """
            update public.materials
            set status = 'processing',
                error_message = null
            where id = $1::uuid and user_id = $2::uuid
            """,
            material_id,
            user_id,
        )
    finally:
        await connection.close()


def _material_response(row: dict[str, object], signed_url: str | None = None) -> MaterialResponse:
    return MaterialResponse(
        id=cast(UUID, row["id"]),
        title=str(row["title"]),
        source_type=cast(SourceType, row["source_type"]),
        file_name=_optional_str(row.get("file_name")),
        file_path=_optional_str(row.get("file_path")),
        mime_type=_optional_str(row.get("mime_type")),
        size_bytes=_optional_int(row.get("size_bytes")),
        page_count=_optional_int(row.get("page_count")),
        lang_detected=_optional_str(row.get("lang_detected")),
        status=cast(MaterialStatus, row["status"]),
        error_message=_optional_str(row.get("error_message")),
        chunks_count=_optional_int(row.get("chunks_count")) or 0,
        signed_url=signed_url,
        created_at=cast(datetime, row["created_at"]),
        updated_at=cast(datetime, row["updated_at"]),
    )


def _optional_str(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _optional_int(value: object) -> int | None:
    return value if isinstance(value, int) else None
