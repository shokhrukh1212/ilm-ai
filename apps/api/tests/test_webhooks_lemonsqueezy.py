import asyncio
import hashlib
import hmac
import json
from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.routers import webhooks_lemonsqueezy as wh
from app.services import billing
from app.settings import settings

USER_ID = "00000000-0000-0000-0000-000000000001"
SECRET = "ls-webhook-secret"


class FakeRequest:
    def __init__(self, raw: bytes) -> None:
        self._raw = raw

    async def body(self) -> bytes:
        return self._raw

    async def json(self) -> Any:
        return json.loads(self._raw)


def _sign(raw: bytes) -> str:
    return hmac.new(SECRET.encode(), raw, hashlib.sha256).hexdigest()


def _body(resp: Any) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(resp.body)
    return data


def _event(event_name: str, status: str = "active") -> bytes:
    payload = {
        "meta": {"event_name": event_name, "custom_data": {"user_id": USER_ID, "plan": "talaba"}},
        "data": {
            "type": "subscriptions",
            "id": "sub_42",
            "attributes": {"status": status, "variant_id": 999, "renews_at": "2026-06-30T00:00:00Z"},
        },
    }
    return json.dumps(payload).encode()


@pytest.fixture(autouse=True)
def _secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "lemonsqueezy_webhook_secret", SECRET)


def test_verify_signature() -> None:
    raw = b'{"a":1}'
    assert wh.verify_signature(raw, _sign(raw), SECRET) is True
    assert wh.verify_signature(raw, "deadbeef", SECRET) is False
    assert wh.verify_signature(raw, None, SECRET) is False


def test_invalid_signature_returns_400(monkeypatch: pytest.MonkeyPatch) -> None:
    activate = AsyncMock()
    monkeypatch.setattr(billing, "activate_subscription", activate)
    raw = _event("subscription_created")
    resp = asyncio.run(
        wh.lemonsqueezy_webhook(FakeRequest(raw), x_signature="wrong")  # type: ignore[arg-type]
    )
    assert resp.status_code == 400
    activate.assert_not_awaited()


def test_subscription_created_activates(monkeypatch: pytest.MonkeyPatch) -> None:
    activate = AsyncMock()
    monkeypatch.setattr(billing, "activate_subscription", activate)
    monkeypatch.setattr(billing, "record_transaction", AsyncMock())
    raw = _event("subscription_created")
    resp = asyncio.run(
        wh.lemonsqueezy_webhook(FakeRequest(raw), x_signature=_sign(raw))  # type: ignore[arg-type]
    )
    assert _body(resp) == {"received": True}
    activate.assert_awaited_once()
    assert activate.await_args is not None
    assert activate.await_args.kwargs["plan"] == "talaba"
    assert activate.await_args.kwargs["provider_sub_id"] == "sub_42"


def test_subscription_expired_deactivates(monkeypatch: pytest.MonkeyPatch) -> None:
    deactivate = AsyncMock()
    monkeypatch.setattr(billing, "deactivate_subscription", deactivate)
    monkeypatch.setattr(billing, "record_transaction", AsyncMock())
    raw = _event("subscription_expired", status="expired")
    asyncio.run(
        wh.lemonsqueezy_webhook(FakeRequest(raw), x_signature=_sign(raw))  # type: ignore[arg-type]
    )
    deactivate.assert_awaited_once_with(USER_ID, "lemonsqueezy")


def test_subscription_cancelled_keeps_access(monkeypatch: pytest.MonkeyPatch) -> None:
    deactivate = AsyncMock()
    record = AsyncMock()
    monkeypatch.setattr(billing, "deactivate_subscription", deactivate)
    monkeypatch.setattr(billing, "record_transaction", record)
    raw = _event("subscription_cancelled", status="cancelled")
    asyncio.run(
        wh.lemonsqueezy_webhook(FakeRequest(raw), x_signature=_sign(raw))  # type: ignore[arg-type]
    )
    deactivate.assert_not_awaited()  # access kept until expiry
    record.assert_awaited_once()
