"""Lemon Squeezy webhook at POST /webhooks/lemonsqueezy.

Lemon Squeezy is a Merchant of Record (replaces Stripe — Stripe doesn't onboard
UZ-based businesses). Events are verified via the ``X-Signature`` header, an
HMAC-SHA256 of the raw request body keyed with the webhook signing secret.

Event mapping (``meta.event_name``):
  subscription_created / subscription_updated(active) -> activate tier
  subscription_expired                                -> deactivate tier
  subscription_cancelled                              -> recorded only (access kept
                                                         until the period ends, when
                                                         an `expired` event arrives)

The Supabase user id travels in the checkout's custom data and comes back as
``meta.custom_data.user_id``.
"""

import hashlib
import hmac
import logging
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse

from ..services import billing
from ..settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Variant id (from Lemon Squeezy) -> our plan. Variant ids arrive as ints in the
# payload, so we compare on the string form.
_VARIANT_TO_PLAN: dict[str, str] = {}
if settings.lemonsqueezy_variant_talaba:
    _VARIANT_TO_PLAN[settings.lemonsqueezy_variant_talaba] = "talaba"
if settings.lemonsqueezy_variant_pro:
    _VARIANT_TO_PLAN[settings.lemonsqueezy_variant_pro] = "pro"


def verify_signature(payload: bytes, signature: str | None, secret: str) -> bool:
    if not signature or not secret:
        return False
    expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def _user_id_from(meta: dict[str, Any]) -> str | None:
    custom = meta.get("custom_data") or {}
    user_id = custom.get("user_id")
    return str(user_id) if user_id else None


def _plan_from(attributes: dict[str, Any], meta: dict[str, Any]) -> str:
    custom = meta.get("custom_data") or {}
    if custom.get("plan"):
        return str(custom["plan"])
    variant_id = attributes.get("variant_id")
    if variant_id is not None and str(variant_id) in _VARIANT_TO_PLAN:
        return _VARIANT_TO_PLAN[str(variant_id)]
    return "talaba"


def _period_end(attributes: dict[str, Any]) -> datetime | None:
    raw = attributes.get("renews_at") or attributes.get("ends_at")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return None


async def _handle_event(event: dict[str, Any]) -> None:
    meta = event.get("meta", {})
    event_name = meta.get("event_name")
    data = event.get("data", {})
    attributes = data.get("attributes", {})
    sub_id = str(data.get("id"))
    user_id = _user_id_from(meta)

    if not user_id:
        logger.warning("Lemon Squeezy %s without user id (sub %s)", event_name, sub_id)
        return

    if event_name in ("subscription_created", "subscription_updated"):
        if attributes.get("status") in ("active", "on_trial", "past_due"):
            await billing.activate_subscription(
                user_id,
                provider="lemonsqueezy",
                plan=_plan_from(attributes, meta),
                provider_sub_id=sub_id,
                period_end=_period_end(attributes),
            )
            await billing.record_transaction(
                user_id=user_id,
                provider="lemonsqueezy",
                provider_tx_id=sub_id,
                state=2,
                raw=event,
            )

    elif event_name == "subscription_expired":
        await billing.deactivate_subscription(user_id, "lemonsqueezy")
        await billing.record_transaction(
            user_id=user_id,
            provider="lemonsqueezy",
            provider_tx_id=sub_id,
            state=-2,
            raw=event,
        )

    elif event_name == "subscription_cancelled":
        # Access stays until the period ends; just record it.
        await billing.record_transaction(
            user_id=user_id,
            provider="lemonsqueezy",
            provider_tx_id=sub_id,
            state=1,
            raw=event,
        )


@router.post("/lemonsqueezy")
async def lemonsqueezy_webhook(
    request: Request,
    x_signature: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    payload = await request.body()
    if not verify_signature(payload, x_signature, settings.lemonsqueezy_webhook_secret):
        return JSONResponse({"error": "invalid signature"}, status_code=400)

    await _handle_event(await request.json())
    return JSONResponse({"received": True})
