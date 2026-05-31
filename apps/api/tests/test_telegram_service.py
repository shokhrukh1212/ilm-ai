import asyncio
import re
from typing import Any
from unittest.mock import AsyncMock

import pytest

from app import db as app_db
from app.services import telegram_service as svc


class FakeTransaction:
    async def __aenter__(self) -> "FakeTransaction":
        return self

    async def __aexit__(self, *_args: Any) -> None:
        return None


class FakeConnection:
    def __init__(self, fetchrow_return: Any = None) -> None:
        self._fetchrow = fetchrow_return
        self.executed: list[tuple[Any, ...]] = []
        self.closed = False

    def transaction(self) -> FakeTransaction:
        return FakeTransaction()

    async def fetchrow(self, *_args: Any) -> Any:
        return self._fetchrow

    async def execute(self, *args: Any) -> str:
        self.executed.append(args)
        return "INSERT 0 1"

    async def close(self) -> None:
        self.closed = True


class TestGenerateCode:
    def test_format(self) -> None:
        code = svc.generate_code()
        assert re.fullmatch(r"[0-9A-F]{8}", code)

    def test_unique_enough(self) -> None:
        assert svc.generate_code() != svc.generate_code()


class TestNormalizeLang:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("uz", "uz-latn"),
            ("UZ", "uz-latn"),
            ("uzc", "uz-cyrl"),
            ("ru", "ru"),
            ("EN", "en"),
            ("  ru  ", "ru"),
            ("xx", None),
        ],
    )
    def test_aliases(self, raw: str, expected: str | None) -> None:
        assert svc.normalize_lang(raw) == expected


class TestParseOptions:
    def test_none(self) -> None:
        assert svc._parse_options(None) is None

    def test_json_string(self) -> None:
        assert svc._parse_options('["a", "b"]') == ["a", "b"]

    def test_list(self) -> None:
        assert svc._parse_options(["a", "b"]) == ["a", "b"]


class TestParsePlanDays:
    def test_none(self) -> None:
        assert svc._parse_plan_days(None) == []

    def test_dict_with_plan(self) -> None:
        assert svc._parse_plan_days({"plan": [{"date": "d"}]}) == [{"date": "d"}]

    def test_json_string(self) -> None:
        assert svc._parse_plan_days('{"plan": [{"date": "d"}]}') == [{"date": "d"}]


class TestRedeemCode:
    def test_returns_none_for_unknown_code(self, monkeypatch: pytest.MonkeyPatch) -> None:
        connection = FakeConnection(fetchrow_return=None)
        monkeypatch.setattr(app_db, "connect", AsyncMock(return_value=connection))
        result = asyncio.run(svc.redeem_code(123, "NOPE"))
        assert result is None
        assert connection.closed


class TestCreateLinkCode:
    def test_inserts_and_returns_code(self, monkeypatch: pytest.MonkeyPatch) -> None:
        connection = FakeConnection()
        monkeypatch.setattr(app_db, "connect", AsyncMock(return_value=connection))
        code = asyncio.run(svc.create_link_code("00000000-0000-0000-0000-000000000001"))
        assert re.fullmatch(r"[0-9A-F]{8}", code)
        # delete prior unlinked rows + insert new row
        assert len(connection.executed) == 2
        assert connection.closed
