from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock
from uuid import UUID
import asyncio

import pytest
from fastapi import BackgroundTasks, HTTPException

from app import db as app_db
from app.routers import materials

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_MATERIAL_ID = UUID("10000000-0000-0000-0000-000000000001")


class FakeConnection:
    def __init__(self, row: dict[str, Any] | None = None, rows: list[dict[str, Any]] | None = None) -> None:
        self.row = row
        self.rows = rows or []
        self.executed: list[tuple[str, tuple[Any, ...]]] = []
        self.closed = False

    async def fetch(self, *_args: Any) -> list[dict[str, Any]]:
        return self.rows

    async def fetchrow(self, *_args: Any) -> dict[str, Any] | None:
        return self.row

    async def execute(self, query: str, *args: Any) -> None:
        self.executed.append((query, args))

    async def close(self) -> None:
        self.closed = True


class FakeStorage:
    bucket = "materials"

    def __init__(self) -> None:
        self.removed: list[str] = []

    async def create_signed_upload_url(self, path: str) -> dict[str, str]:
        return {
            "signed_url": f"https://storage.example/upload/{path}",
            "token": "signed-token",
            "path": path,
        }

    async def create_signed_read_url(self, path: str) -> str:
        return f"https://storage.example/read/{path}"

    async def remove(self, path: str) -> None:
        self.removed.append(path)


def material_row(**overrides: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "id": TEST_MATERIAL_ID,
        "user_id": UUID(TEST_USER_ID),
        "title": "Algebra",
        "source_type": "pdf",
        "file_name": "algebra.pdf",
        "file_path": f"{TEST_USER_ID}/{TEST_MATERIAL_ID}/algebra.pdf",
        "mime_type": "application/pdf",
        "size_bytes": 1200,
        "page_count": 30,
        "lang_detected": "ru",
        "status": "ready",
        "error_message": None,
        "chunks_count": 12,
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
        "updated_at": datetime(2026, 1, 1, tzinfo=UTC),
    }
    row.update(overrides)
    return row


def test_list_materials(monkeypatch: pytest.MonkeyPatch) -> None:
    connection = FakeConnection(rows=[material_row()])
    monkeypatch.setattr(app_db, "connect", AsyncMock(return_value=connection))

    response = asyncio.run(materials.list_materials(TEST_USER_ID))

    assert response[0].title == "Algebra"
    assert response[0].chunks_count == 12


def test_create_signed_upload_url_inserts_processing_material(monkeypatch: pytest.MonkeyPatch) -> None:
    connection = FakeConnection(row=material_row(status="processing", page_count=None, chunks_count=0))
    storage = FakeStorage()
    monkeypatch.setattr(app_db, "connect", AsyncMock(return_value=connection))
    monkeypatch.setattr(materials, "get_storage_service", lambda: storage)

    response = asyncio.run(
        materials.create_upload_url(
            materials.UploadUrlRequest(
                filename="algebra.pdf",
                content_type="application/pdf",
                size_bytes=1200,
            ),
            TEST_USER_ID,
        )
    )

    assert response.bucket == "materials"
    assert response.token == "signed-token"
    assert response.path.endswith("/algebra.pdf")


def test_paste_material_queues_ingest(monkeypatch: pytest.MonkeyPatch) -> None:
    connection = FakeConnection(
        row=material_row(
            source_type="paste",
            file_name=None,
            file_path=None,
            mime_type="text/plain",
            status="processing",
            chunks_count=0,
        )
    )
    ingest = AsyncMock()
    background = BackgroundTasks()
    monkeypatch.setattr(app_db, "connect", AsyncMock(return_value=connection))
    monkeypatch.setattr(materials, "ingest_paste_material", ingest)

    response = asyncio.run(
        materials.paste_material(
            materials.PasteRequest(title="Notes", content="Long enough pasted text"),
            background,
            TEST_USER_ID,
        )
    )
    asyncio.run(background())

    assert response.source_type == "paste"
    assert ingest.await_count == 1


def test_delete_material_removes_storage_and_row(monkeypatch: pytest.MonkeyPatch) -> None:
    connection = FakeConnection(row=material_row())
    storage = FakeStorage()
    monkeypatch.setattr(app_db, "connect", AsyncMock(return_value=connection))
    monkeypatch.setattr(materials, "get_storage_service", lambda: storage)

    response = asyncio.run(materials.delete_material(TEST_MATERIAL_ID, TEST_USER_ID))

    assert response.status_code == 204
    assert storage.removed == [f"{TEST_USER_ID}/{TEST_MATERIAL_ID}/algebra.pdf"]
    assert any("delete from public.materials" in query for query, _ in connection.executed)


def test_upload_url_rejects_unsupported_file_type(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(app_db, "connect", AsyncMock())

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            materials.create_upload_url(
                materials.UploadUrlRequest(
                    filename="image.png",
                    content_type="image/png",
                    size_bytes=100,
                ),
                TEST_USER_ID,
            )
        )

    assert exc_info.value.status_code == 400
