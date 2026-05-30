import asyncio
import json
from typing import Any
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app import db as app_db
from app.routers import quiz
from app.routers.quiz import GenerateRequest, _owned_session, _parse_options, _question_public

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_MATERIAL_ID = "10000000-0000-0000-0000-000000000001"
TEST_SESSION_ID = "20000000-0000-0000-0000-000000000001"


class FakeConnection:
    def __init__(self, fetchrow_return: Any = None) -> None:
        self._fetchrow = fetchrow_return
        self.closed = False

    async def fetchrow(self, *_args: Any) -> Any:
        return self._fetchrow

    async def close(self) -> None:
        self.closed = True


class TestGenerateRequestValidation:
    def test_defaults(self) -> None:
        req = GenerateRequest(material_id=UUID(TEST_MATERIAL_ID))
        assert req.num_questions == 10
        assert req.difficulty == "medium"
        assert req.lang is None

    def test_rejects_too_few_questions(self) -> None:
        with pytest.raises(ValidationError):
            GenerateRequest(material_id=UUID(TEST_MATERIAL_ID), num_questions=4)

    def test_rejects_too_many_questions(self) -> None:
        with pytest.raises(ValidationError):
            GenerateRequest(material_id=UUID(TEST_MATERIAL_ID), num_questions=21)

    def test_rejects_invalid_difficulty(self) -> None:
        with pytest.raises(ValidationError):
            GenerateRequest(material_id=UUID(TEST_MATERIAL_ID), difficulty="impossible")  # type: ignore[arg-type]


class TestParseOptions:
    def test_none(self) -> None:
        assert _parse_options(None) is None

    def test_json_string(self) -> None:
        assert _parse_options(json.dumps(["a", "b", "c", "d"])) == ["a", "b", "c", "d"]

    def test_list(self) -> None:
        assert _parse_options(["a", "b"]) == ["a", "b"]


class TestQuestionPublic:
    def test_maps_row(self) -> None:
        row = {"id": 7, "type": "mcq", "prompt": "Q", "options": json.dumps(["a", "b", "c", "d"])}
        pub = _question_public(row)
        assert pub.id == 7
        assert pub.type == "mcq"
        assert pub.options == ["a", "b", "c", "d"]


class TestOwnership:
    def test_owned_session_raises_404_when_missing(self) -> None:
        connection = FakeConnection(fetchrow_return=None)
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(_owned_session(connection, TEST_SESSION_ID, TEST_USER_ID))
        assert exc_info.value.status_code == 404

    def test_generate_raises_404_when_material_not_owned(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        connection = FakeConnection(fetchrow_return=None)
        monkeypatch.setattr(app_db, "connect", AsyncMock(return_value=connection))
        req = GenerateRequest(material_id=UUID(TEST_MATERIAL_ID))
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(quiz.generate(req, TEST_USER_ID))
        assert exc_info.value.status_code == 404

    def test_generate_raises_409_when_material_not_ready(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        connection = FakeConnection(
            fetchrow_return={"status": "processing", "lang_detected": "uz-latn"}
        )
        monkeypatch.setattr(app_db, "connect", AsyncMock(return_value=connection))
        req = GenerateRequest(material_id=UUID(TEST_MATERIAL_ID))
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(quiz.generate(req, TEST_USER_ID))
        assert exc_info.value.status_code == 409
