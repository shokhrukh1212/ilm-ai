"""Stripe webhook at POST /webhooks/stripe.

Signature-verified via ``stripe.Webhook.construct_event``. Activates the tier on
``checkout.session.completed``, rolls the period on ``customer.subscription.updated``,
and deactivates on ``customer.subscription.deleted``. The user id travels in
``client_reference_id`` / subscription metadata set at checkout.
"""

import logging
from datetime import datetime, timezone
from typing import Annotated, Any

import stripe
from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse

from ..services import billing
from ..settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Stripe price id → plan (inverse of the checkout map).
_PRICE_TO_PLAN: dict[str, str] = {}
if settings.stripe_price_talaba:
    _PRICE_TO_PLAN[settings.stripe_price_talaba] = "talaba"
if settings.stripe_price_pro:
    _PRICE_TO_PLAN[settings.stripe_price_pro] = "pro"


def _user_id_from(obj: dict[str, Any]) -> str | None:
    return obj.get("client_reference_id") or (obj.get("metadata") or {}).get("user_id")


def _plan_from(obj: dict[str, Any]) -> str:
    meta_plan = (obj.get("metadata") or {}).get("plan")
    if meta_plan:
        return str(meta_plan)
    # Fall back to the price on the first line/subscription item.
    try:
        items = obj.get("items", {}).get("data", [])
        price_id = items[0]["price"]["id"] if items else None
        if price_id and price_id in _PRICE_TO_PLAN:
            return _PRICE_TO_PLAN[price_id]
    except (KeyError, IndexError, TypeError):
        pass
    return "talaba"


def _period_end(obj: dict[str, Any]) -> datetime | None:
    ts = obj.get("current_period_end")
    return datetime.fromtimestamp(int(ts), tz=timezone.utc) if ts else None


async def _handle_event(event: dict[str, Any]) -> None:
    event_type = event.get("type")
    obj = event.get("data", {}).get("object", {})

    if event_type == "checkout.session.completed":
        user_id = _user_id_from(obj)
        if not user_id:
            logger.warning("Stripe checkout.completed without user id: %s", obj.get("id"))
            return
        await billing.activate_subscription(
            user_id,
            provider="stripe",
            plan=_plan_from(obj),
            provider_sub_id=obj.get("subscription"),
        )
        await billing.record_transaction(
            user_id=user_id,
            provider="stripe",
            provider_tx_id=str(obj.get("id")),
            state=2,
            amount_usd=(obj.get("amount_total") or 0) / 100 or None,
            raw=obj,
        )

    elif event_type == "customer.subscription.updated":
        user_id = _user_id_from(obj)
        if not user_id:
            return
        # Stripe marks a scheduled cancel with cancel_at_period_end; an ended sub
        # arrives as a separate `deleted` event handled below.
        if obj.get("status") == "active":
            await billing.activate_subscription(
                user_id,
                provider="stripe",
                plan=_plan_from(obj),
                provider_sub_id=obj.get("id"),
                period_end=_period_end(obj),
            )

    elif event_type == "customer.subscription.deleted":
        user_id = _user_id_from(obj)
        if not user_id:
            return
        await billing.deactivate_subscription(user_id, "stripe")
        await billing.record_transaction(
            user_id=user_id,
            provider="stripe",
            provider_tx_id=str(obj.get("id")),
            state=-2,
            raw=obj,
        )


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(  # type: ignore[no-untyped-call]
            payload, stripe_signature, settings.stripe_webhook_secret
        )
    except (ValueError, stripe.SignatureVerificationError):
        return JSONResponse({"error": "invalid signature"}, status_code=400)

    await _handle_event(dict(event))
    return JSONResponse({"received": True})
