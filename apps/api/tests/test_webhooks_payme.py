import asyncio
import base64
import json
from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.routers import webhooks_payme as wh
from app.services import billing
from app.settings import settings

USER_ID = "00000000-0000-0000-0000-000000000001"
KEY = "merchant-key"
AMOUNT_TIYIN = 29000 * 100


class FakeRequest:
    def __init__(self, body: dict[str, Any]) -> None:
        self._body = body

    async def json(self) -> dict[str, Any]:
        return self._body


def _auth(key: str = KEY) -> str:
    return "Basic " + base64.b64encode(f"Paycom:{key}".encode()).decode()


def _body(resp: Any) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(resp.body)
    return data


@pytest.fixture(autouse=True)
def _key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "payme_key", KEY)


def test_basic_auth_helper() -> None:
    assert wh.check_basic_auth(_auth(), KEY) is True
    assert wh.check_basic_auth(_auth("wrong"), KEY) is False
    assert wh.check_basic_auth(None, KEY) is False
    assert wh.check_basic_auth("Bearer x", KEY) is False


def test_bad_auth_returns_32504() -> None:
    req = FakeRequest({"method": "CheckPerformTransaction", "params": {}, "id": 1})
    resp = asyncio.run(wh.payme_webhook(req, authorization="Basic bad"))  # type: ignore[arg-type]
    assert _body(resp)["error"]["code"] == wh.ERR_INSUFFICIENT_PRIVILEGE


def test_check_perform_amount_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(billing, "user_exists", AsyncMock(return_value=True))
    req = FakeRequest(
        {
            "method": "CheckPerformTransaction",
            "params": {"amount": 5000, "account": {"user_id": USER_ID}},
            "id": 1,
        }
    )
    resp = asyncio.run(wh.payme_webhook(req, authorization=_auth()))  # type: ignore[arg-type]
    assert _body(resp)["error"]["code"] == wh.ERR_INVALID_AMOUNT


def test_check_perform_allows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(billing, "user_exists", AsyncMock(return_value=True))
    req = FakeRequest(
        {
            "method": "CheckPerformTransaction",
            "params": {"amount": AMOUNT_TIYIN, "account": {"user_id": USER_ID}},
            "id": 1,
        }
    )
    resp = asyncio.run(wh.payme_webhook(req, authorization=_auth()))  # type: ignore[arg-type]
    assert _body(resp)["result"] == {"allow": True}


def test_unknown_account_returns_account_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(billing, "user_exists", AsyncMock(return_value=False))
    req = FakeRequest(
        {
            "method": "CheckPerformTransaction",
            "params": {"amount": AMOUNT_TIYIN, "account": {"user_id": USER_ID}},
            "id": 1,
        }
    )
    resp = asyncio.run(wh.payme_webhook(req, authorization=_auth()))  # type: ignore[arg-type]
    assert _body(resp)["error"]["code"] == wh.ERR_ACCOUNT_NOT_FOUND


def test_perform_activates_subscription(monkeypatch: pytest.MonkeyPatch) -> None:
    activate = AsyncMock()
    monkeypatch.setattr(billing, "activate_subscription", activate)
    monkeypatch.setattr(billing, "record_transaction", AsyncMock())
    monkeypatch.setattr(
        billing,
        "get_transaction",
        AsyncMock(
            return_value={
                "user_id": USER_ID,
                "state": wh.STATE_CREATED,
                "amount_uzs": 29000,
                "raw": {"create_time": 123},
            }
        ),
    )
    req = FakeRequest({"method": "PerformTransaction", "params": {"id": "tx1"}, "id": 1})
    resp = asyncio.run(wh.payme_webhook(req, authorization=_auth()))  # type: ignore[arg-type]
    result = _body(resp)["result"]
    assert result["state"] == wh.STATE_PERFORMED
    activate.assert_awaited_once_with(USER_ID, provider="payme", plan="talaba")


def test_perform_unknown_transaction(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(billing, "get_transaction", AsyncMock(return_value=None))
    req = FakeRequest({"method": "PerformTransaction", "params": {"id": "nope"}, "id": 1})
    resp = asyncio.run(wh.payme_webhook(req, authorization=_auth()))  # type: ignore[arg-type]
    assert _body(resp)["error"]["code"] == wh.ERR_TRANSACTION_NOT_FOUND


def test_unknown_method(monkeypatch: pytest.MonkeyPatch) -> None:
    req = FakeRequest({"method": "DoMagic", "params": {}, "id": 1})
    resp = asyncio.run(wh.payme_webhook(req, authorization=_auth()))  # type: ignore[arg-type]
    assert _body(resp)["error"]["code"] == wh.ERR_METHOD_NOT_FOUND
