import asyncio
from typing import Any

import pytest

from app import db
from app.services import billing


def test_tier_for_plan() -> None:
    assert billing.tier_for_plan("talaba") == "talaba"
    assert billing.tier_for_plan("pro") == "pro"
    assert billing.tier_for_plan("team") == "team"
    assert billing.tier_for_plan("free") == "free"
    assert billing.tier_for_plan("nonsense") == "free"


def test_price_uzs_for_plan() -> None:
    assert billing.price_uzs_for_plan("talaba") == 29000
    assert billing.price_uzs_for_plan("pro") == 79000
    assert billing.price_uzs_for_plan("unknown") is None


class FakeConn:
    """Records execute/fetchrow calls so we can assert on tier + period writes."""

    def __init__(self, fetch_results: list[Any] | None = None) -> None:
        self.executed: list[tuple[Any, ...]] = []
        self._fetch_results = fetch_results or []

    def transaction(self) -> "FakeConn":
        return self

    async def __aenter__(self) -> "FakeConn":
        return self

    async def __aexit__(self, *args: Any) -> None:
        return None

    async def execute(self, query: str, *args: Any) -> None:
        self.executed.append((query, *args))

    async def fetchrow(self, query: str, *args: Any) -> Any:
        return self._fetch_results.pop(0) if self._fetch_results else None

    async def close(self) -> None:
        return None


def _patch_conn(monkeypatch: pytest.MonkeyPatch, conn: FakeConn) -> None:
    async def fake_connect() -> FakeConn:
        return conn

    monkeypatch.setattr(db, "connect", fake_connect)


def test_activate_sets_tier_and_default_period(monkeypatch: pytest.MonkeyPatch) -> None:
    conn = FakeConn()
    _patch_conn(monkeypatch, conn)

    asyncio.run(
        billing.activate_subscription("u1", provider="payme", plan="talaba")
    )

    # subscription insert + user tier update both ran.
    queries = " ".join(q[0] for q in conn.executed)
    assert "INSERT INTO public.subscriptions" in queries
    assert "UPDATE public.users SET tier" in queries
    # tier value passed is the plan's tier.
    tier_update = next(q for q in conn.executed if "SET tier" in q[0])
    assert tier_update[2] == "talaba"
    # a period_end was supplied (default +30 days).
    insert = next(q for q in conn.executed if "INSERT INTO public.subscriptions" in q[0])
    assert insert[-1] is not None


def test_deactivate_drops_tier_to_free(monkeypatch: pytest.MonkeyPatch) -> None:
    conn = FakeConn()
    _patch_conn(monkeypatch, conn)

    asyncio.run(billing.deactivate_subscription("u1", "stripe"))

    tier_update = next(q for q in conn.executed if "SET tier" in q[0])
    assert "'free'" in tier_update[0]


def test_cancel_at_period_end(monkeypatch: pytest.MonkeyPatch) -> None:
    conn = FakeConn()
    _patch_conn(monkeypatch, conn)

    asyncio.run(billing.cancel_at_period_end("u1"))

    assert any("cancel_at_period_end" in q[0] for q in conn.executed)
