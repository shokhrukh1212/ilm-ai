"""Subscription + payment ledger access for the billing router and payment webhooks.

All access uses the service-role asyncpg connection (``db.connect``), which bypasses
RLS, so every query filters by ``user_id`` explicitly — the same pattern every other
router/service in this app follows.

Amounts in ``payment_transactions.amount_uzs`` are integer UZS (NOT tiyin). The Payme
webhook divides incoming tiyin by 100 before calling :func:`record_transaction`.
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from .. import db
from ..settings import settings

# A plan maps onto exactly one user tier. 'free' is the default with no subscription.
PLAN_TO_TIER: dict[str, str] = {
    "talaba": "talaba",
    "pro": "pro",
    "team": "team",
}

# Plan price in UZS, used to validate Payme/Click webhook amounts.
PLAN_PRICE_UZS: dict[str, int] = {
    "talaba": settings.price_talaba_uzs,
    "pro": settings.price_pro_uzs,
    "team": settings.price_team_uzs,
}

DEFAULT_PERIOD_DAYS = 30


def tier_for_plan(plan: str) -> str:
    return PLAN_TO_TIER.get(plan, "free")


def price_uzs_for_plan(plan: str) -> int | None:
    return PLAN_PRICE_UZS.get(plan)


async def activate_subscription(
    user_id: str,
    provider: str,
    plan: str,
    provider_sub_id: str | None = None,
    card_token: str | None = None,
    period_end: datetime | None = None,
) -> None:
    """Mark the subscription active and bump the user's tier.

    Idempotent: a repeated webhook for the same active subscription just refreshes the
    period end. Period rollover defaults to +30 days when the provider gives no date.
    """
    tier = tier_for_plan(plan)
    end = period_end or (datetime.now(timezone.utc) + timedelta(days=DEFAULT_PERIOD_DAYS))

    connection = await db.connect()
    try:
        async with connection.transaction():
            await connection.execute(
                """
                INSERT INTO public.subscriptions
                  (user_id, provider, provider_sub_id, card_token, plan, status,
                   current_period_end, updated_at)
                VALUES ($1::uuid, $2, $3, $4, $5, 'active', $6, now())
                """,
                user_id,
                provider,
                provider_sub_id,
                card_token,
                plan,
                end,
            )
            await connection.execute(
                "UPDATE public.users SET tier = $2 WHERE id = $1::uuid",
                user_id,
                tier,
            )
    finally:
        await connection.close()


async def deactivate_subscription(user_id: str, provider: str) -> None:
    """Cancel the user's active subscriptions for a provider and drop tier to free."""
    connection = await db.connect()
    try:
        async with connection.transaction():
            await connection.execute(
                """
                UPDATE public.subscriptions
                SET status = 'cancelled', updated_at = now()
                WHERE user_id = $1::uuid AND provider = $2
                  AND status IN ('active', 'past_due', 'cancel_at_period_end')
                """,
                user_id,
                provider,
            )
            await connection.execute(
                "UPDATE public.users SET tier = 'free' WHERE id = $1::uuid",
                user_id,
            )
    finally:
        await connection.close()


async def cancel_at_period_end(user_id: str) -> None:
    """User-initiated cancel: keep the tier until ``current_period_end`` elapses."""
    connection = await db.connect()
    try:
        await connection.execute(
            """
            UPDATE public.subscriptions
            SET status = 'cancel_at_period_end', updated_at = now()
            WHERE user_id = $1::uuid AND status = 'active'
            """,
            user_id,
        )
    finally:
        await connection.close()


async def record_transaction(
    user_id: str | None,
    provider: str,
    provider_tx_id: str,
    state: int,
    raw: dict[str, Any],
    amount_uzs: int | None = None,
    amount_usd: float | None = None,
) -> None:
    """Idempotent upsert into the payment ledger keyed on (provider, provider_tx_id)."""
    connection = await db.connect()
    try:
        await connection.execute(
            """
            INSERT INTO public.payment_transactions
              (user_id, provider, provider_tx_id, amount_uzs, amount_usd, state, raw,
               updated_at)
            VALUES ($1::uuid, $2, $3, $4, $5, $6, $7::jsonb, now())
            ON CONFLICT (provider, provider_tx_id) DO UPDATE
              SET state = excluded.state,
                  amount_uzs = coalesce(excluded.amount_uzs, public.payment_transactions.amount_uzs),
                  amount_usd = coalesce(excluded.amount_usd, public.payment_transactions.amount_usd),
                  raw = excluded.raw,
                  updated_at = now()
            """,
            user_id,
            provider,
            provider_tx_id,
            amount_uzs,
            amount_usd,
            state,
            json.dumps(raw, ensure_ascii=False, default=str),
        )
    finally:
        await connection.close()


async def get_transaction(provider: str, provider_tx_id: str) -> dict[str, Any] | None:
    """Read a ledger row by provider id (Payme state machine lookups)."""
    connection = await db.connect()
    try:
        row = await connection.fetchrow(
            """
            SELECT user_id::text AS user_id, provider, provider_tx_id, amount_uzs,
                   state, raw, created_at
            FROM public.payment_transactions
            WHERE provider = $1 AND provider_tx_id = $2
            """,
            provider,
            provider_tx_id,
        )
    finally:
        await connection.close()
    if row is None:
        return None
    result = dict(row)
    raw = result.get("raw")
    if isinstance(raw, str):
        result["raw"] = json.loads(raw)
    return result


async def get_subscription(user_id: str) -> dict[str, Any]:
    """Current tier + latest subscription row, for the /billing page."""
    connection = await db.connect()
    try:
        user = await connection.fetchrow(
            "SELECT tier FROM public.users WHERE id = $1::uuid",
            user_id,
        )
        sub = await connection.fetchrow(
            """
            SELECT provider, plan, status, current_period_end, created_at
            FROM public.subscriptions
            WHERE user_id = $1::uuid
            ORDER BY created_at DESC
            LIMIT 1
            """,
            user_id,
        )
    finally:
        await connection.close()

    return {
        "tier": (user["tier"] if user else None) or "free",
        "subscription": dict(sub) if sub else None,
    }


async def user_exists(user_id: str) -> bool:
    """Validate that a webhook-supplied account id maps to a real user."""
    connection = await db.connect()
    try:
        row = await connection.fetchrow(
            "SELECT 1 FROM public.users WHERE id = $1::uuid",
            user_id,
        )
    finally:
        await connection.close()
    return row is not None
