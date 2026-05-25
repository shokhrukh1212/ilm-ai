import asyncio
import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from fastapi import HTTPException

from app import db as app_db
from app.routers import chat
from app.routers.chat import ChatRequest

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_MATERIAL_ID = "10000000-0000-0000-0000-000000000001"
TEST_SESSION_ID = "20000000-0000-0000-0000-000000000001"


class FakeConnection:
    def __init__(self, fetchval_return: Any = None, fetchrow_return: Any = None) -> None:
        self._fetchval = fetchval_return
        self._fetchrow = fetchrow_return
        self.executed: list[tuple[str, tuple[Any, ...]]] = []
        self.closed = False

    async def fetchval(self, *_args: Any) -> Any:
        return self._fetchval

    async def fetchrow(self, *_args: Any) -> Any:
        return self._fetchrow

    async def execute(self, query: str, *args: Any) -> None:
        self.executed.append((query, args))

    async def close(self) -> None:
        self.closed = True


def _make_request(session_id: UUID | None = None) -> ChatRequest:
    return ChatRequest(
        material_ids=[UUID(TEST_MATERIAL_ID)],
        message="Fotosintez nima?",
        session_id=session_id,
    )


class TestChatOwnershipCheck:
    def test_raises_404_when_material_not_owned(self, monkeypatch: pytest.MonkeyPatch) -> None:
        connection = FakeConnection(fetchval_return=0)
        monkeypatch.setattr(app_db, "connect", AsyncMock(return_value=connection))

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(chat.chat(_make_request(), TEST_USER_ID))

        assert exc_info.value.status_code == 404

    def test_raises_404_when_count_less_than_requested(self, monkeypatch: pytest.MonkeyPatch) -> None:
        connection = FakeConnection(fetchval_return=0)
        monkeypatch.setattr(app_db, "connect", AsyncMock(return_value=connection))

        req = ChatRequest(
            material_ids=[UUID(TEST_MATERIAL_ID), UUID("30000000-0000-0000-0000-000000000001")],
            message="Q",
        )
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(chat.chat(req, TEST_USER_ID))
        assert exc_info.value.status_code == 404


class TestEnsureSession:
    def test_creates_new_session_when_none_provided(self, monkeypatch: pytest.MonkeyPatch) -> None:
        connection = FakeConnection(fetchval_return=TEST_SESSION_ID)
        monkeypatch.setattr(app_db, "connect", AsyncMock(return_value=connection))

        sid = asyncio.run(
            chat._ensure_session(TEST_USER_ID, [TEST_MATERIAL_ID], "Hello", None)
        )
        assert sid == TEST_SESSION_ID

    def test_reuses_existing_session(self, monkeypatch: pytest.MonkeyPatch) -> None:
        existing_row = {"id": TEST_SESSION_ID}
        connection = FakeConnection(fetchrow_return=existing_row)
        monkeypatch.setattr(app_db, "connect", AsyncMock(return_value=connection))

        sid = asyncio.run(
            chat._ensure_session(TEST_USER_ID, [TEST_MATERIAL_ID], "Hello", TEST_SESSION_ID)
        )
        assert sid == TEST_SESSION_ID


class TestSaveMessages:
    def test_save_user_message_executes_insert(self, monkeypatch: pytest.MonkeyPatch) -> None:
        connection = FakeConnection()
        monkeypatch.setattr(app_db, "connect", AsyncMock(return_value=connection))

        asyncio.run(chat._save_user_message(TEST_SESSION_ID, "Fotosintez nima?"))

        assert connection.closed
        assert len(connection.executed) == 1
        query, args = connection.executed[0]
        assert "INSERT INTO public.chat_messages" in query
        assert "'user'" in query or "user" in query

    def test_save_assistant_message_includes_citations(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.agents.tutor import TutorUsage

        connection = FakeConnection()
        monkeypatch.setattr(app_db, "connect", AsyncMock(return_value=connection))
        usage = TutorUsage(tokens_in=100, tokens_out=200)
        citations = [{"index": 1, "chunk_id": 1, "page": 3}]

        asyncio.run(
            chat._save_assistant_message(TEST_SESSION_ID, "Answer", citations, usage, 1500)
        )

        assert connection.closed
        assert len(connection.executed) == 1
        query, args = connection.executed[0]
        assert "INSERT INTO public.chat_messages" in query
        assert "'assistant'" in query or "assistant" in query
