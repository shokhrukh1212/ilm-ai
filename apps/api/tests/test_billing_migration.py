from pathlib import Path


def test_billing_migration_tables_and_rls() -> None:
    sql = Path("migrations/0007_billing.sql").read_text()

    assert "create table if not exists public.subscriptions" in sql
    assert "create table if not exists public.payment_transactions" in sql

    # subscriptions shape
    assert "provider text check (provider in ('payme', 'click', 'lemonsqueezy'))" in sql
    assert "plan text check (plan in ('talaba', 'pro', 'team'))" in sql
    assert "current_period_end timestamptz" in sql

    # ledger shape + idempotency
    assert "amount_uzs bigint" in sql
    assert "amount_usd numeric" in sql
    assert "payment_transactions_provider_tx_idx" in sql
    assert "(provider, provider_tx_id)" in sql

    # RLS
    assert "alter table public.subscriptions enable row level security" in sql
    assert "alter table public.payment_transactions enable row level security" in sql
    assert "create policy subscriptions_self" in sql
    assert "create policy payment_transactions_self" in sql
    assert "auth.uid() = user_id" in sql
