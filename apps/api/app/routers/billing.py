"""Authenticated billing endpoints: start checkout, cancel, read current subscription.

Checkout returns a redirect URL the browser opens. Tier activation happens
asynchronously in the provider webhooks (webhooks_payme/click/lemonsqueezy), never here.
"""

import base64
import logging
from datetime import datetime
from typing import Annotated, Any, Literal
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..auth import get_current_user_id
from ..services import billing
from ..settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])

Provider = Literal["payme", "click", "lemonsqueezy"]
Plan = Literal["talaba", "pro", "team"]


class CheckoutRequest(BaseModel):
    plan: Plan
    provider: Provider


class CheckoutResponse(BaseModel):
    url: str


class SubscriptionOut(BaseModel):
    provider: str | None
    plan: str | None
    status: str | None
    current_period_end: datetime | None
    created_at: datetime | None


class BillingStatus(BaseModel):
    tier: str
    subscription: SubscriptionOut | None


# Maps each plan to its Lemon Squeezy variant id env var.
_LS_VARIANT_FOR_PLAN: dict[str, str] = {
    "talaba": settings.lemonsqueezy_variant_talaba,
    "pro": settings.lemonsqueezy_variant_pro,
}

LEMONSQUEEZY_API = "https://api.lemonsqueezy.com/v1/checkouts"


async def _user_email(user_id: str) -> str | None:
    """Best-effort email to prefill the Lemon Squeezy checkout (non-fatal if absent)."""
    url = f"{settings.supabase_url}/rest/v1/users"
    headers = {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "Accept": "application/json",
    }
    params = {"id": f"eq.{user_id}", "select": "email"}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, params=params)
        rows = resp.json() if resp.status_code == 200 else []
        return rows[0]["email"] if rows else None
    except Exception:  # pragma: no cover - email is optional
        return None


def _payme_checkout_url(user_id: str, plan: str, amount_uzs: int) -> str:
    # Payme hosted checkout: base64(m=MERCHANT;ac.user_id=...;a=<tiyin>;c=<return>).
    return_url = f"{settings.frontend_url}/billing?status=success"
    payload = (
        f"m={settings.payme_id};ac.user_id={user_id};"
        f"a={amount_uzs * 100};c={return_url}"
    )
    encoded = base64.b64encode(payload.encode("utf-8")).decode("ascii")
    return f"https://checkout.paycom.uz/{encoded}"


def _click_checkout_url(user_id: str, amount_uzs: int) -> str:
    return_url = f"{settings.frontend_url}/billing?status=success"
    query = urlencode(
        {
            "service_id": settings.click_service_id,
            "merchant_id": settings.click_merchant_id,
            "amount": amount_uzs,
            "transaction_param": user_id,
            "return_url": return_url,
        }
    )
    return f"https://my.click.uz/services/pay?{query}"


async def _lemonsqueezy_checkout_url(user_id: str, plan: str) -> str:
    variant_id = _LS_VARIANT_FOR_PLAN.get(plan)
    if not variant_id or not settings.lemonsqueezy_store_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Lemon Squeezy variant for plan '{plan}' is not configured",
        )

    checkout_data: dict[str, Any] = {"custom": {"user_id": user_id, "plan": plan}}
    email = await _user_email(user_id)
    if email:
        checkout_data["email"] = email

    body = {
        "data": {
            "type": "checkouts",
            "attributes": {
                "checkout_data": checkout_data,
                "product_options": {
                    "redirect_url": f"{settings.frontend_url}/billing?status=success",
                },
            },
            "relationships": {
                "store": {
                    "data": {"type": "stores", "id": settings.lemonsqueezy_store_id}
                },
                "variant": {"data": {"type": "variants", "id": variant_id}},
            },
        }
    }
    headers = {
        "Authorization": f"Bearer {settings.lemonsqueezy_api_key}",
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(LEMONSQUEEZY_API, json=body, headers=headers)
    if resp.status_code >= 300:
        logger.error("Lemon Squeezy checkout failed: %s %s", resp.status_code, resp.text)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not create Lemon Squeezy checkout",
        )
    url = resp.json().get("data", {}).get("attributes", {}).get("url")
    if not url:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Lemon Squeezy did not return a checkout URL",
        )
    return str(url)


@router.post("/checkout")
async def checkout(
    req: CheckoutRequest,
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> CheckoutResponse:
    if req.provider == "lemonsqueezy":
        return CheckoutResponse(url=await _lemonsqueezy_checkout_url(user_id, req.plan))

    amount_uzs = billing.price_uzs_for_plan(req.plan)
    if amount_uzs is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown plan"
        )
    if req.provider == "payme":
        return CheckoutResponse(url=_payme_checkout_url(user_id, req.plan, amount_uzs))
    return CheckoutResponse(url=_click_checkout_url(user_id, amount_uzs))


@router.post("/cancel")
async def cancel(
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> dict[str, bool]:
    await billing.cancel_at_period_end(user_id)
    return {"ok": True}


@router.get("")
async def get_billing(
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> BillingStatus:
    data = await billing.get_subscription(user_id)
    sub = data["subscription"]
    return BillingStatus(
        tier=data["tier"],
        subscription=SubscriptionOut(**sub) if sub else None,
    )
