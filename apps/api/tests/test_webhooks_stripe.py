import asyncio
import json
from typing import Any
from unittest.mock import AsyncMock

import pytest
import stripe

from app.routers import webhooks_stripe as wh
from app.services import billing

USER_ID = "00000000-0000-0000-0000-000000000001"


class FakeRequest:
    def __init__(self, raw: bytes = b"{}") -> None:
        self._raw = raw

    async def body(self) -> bytes:
        return self._raw


def _body(resp: Any) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(resp.body)
    return data


def test_invalid_signature_returns_400(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*args: Any, **kwargs: Any) -> Any:
        raise stripe.SignatureVerificationError(  # type: ignore[no-untyped-call]
            "bad sig", "sig-header"
        )

    monkeypatch.setattr(stripe.Webhook, "construct_event", boom)
    resp = asyncio.run(
        wh.stripe_webhook(FakeRequest(), stripe_signature="x")  # type: ignore[arg-type]
    )
    assert resp.status_code == 400


def test_checkout_completed_activates(monkeypatch: pytest.MonkeyPatch) -> None:
    activate = AsyncMock()
    monkeypatch.setattr(billing, "activate_subscription", activate)
    monkeypatch.setattr(billing, "record_transaction", AsyncMock())

    event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_1",
                "client_reference_id": USER_ID,
                "subscription": "sub_1",
                "metadata": {"user_id": USER_ID, "plan": "talaba"},
                "amount_total": 240,
            }
        },
    }
    monkeypatch.setattr(stripe.Webhook, "construct_event", lambda *a, **k: event)

    resp = asyncio.run(
        wh.stripe_webhook(FakeRequest(), stripe_signature="x")  # type: ignore[arg-type]
    )
    assert _body(resp) == {"received": True}
    activate.assert_awaited_once()
    assert activate.await_args is not None
    assert activate.await_args.kwargs["plan"] == "talaba"
    assert activate.await_args.kwargs["provider_sub_id"] == "sub_1"


def test_subscription_deleted_deactivates(monkeypatch: pytest.MonkeyPatch) -> None:
    deactivate = AsyncMock()
    monkeypatch.setattr(billing, "deactivate_subscription", deactivate)
    monkeypatch.setattr(billing, "record_transaction", AsyncMock())

    event = {
        "type": "customer.subscription.deleted",
        "data": {"object": {"id": "sub_1", "metadata": {"user_id": USER_ID}}},
    }
    monkeypatch.setattr(stripe.Webhook, "construct_event", lambda *a, **k: event)

    asyncio.run(wh.stripe_webhook(FakeRequest(), stripe_signature="x"))  # type: ignore[arg-type]
    deactivate.assert_awaited_once_with(USER_ID, "stripe")
