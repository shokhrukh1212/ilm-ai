-- Phase 7: subscriptions + payment transactions (Payme, Click, Stripe) with per-user RLS
create table if not exists public.subscriptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  provider text check (provider in ('payme', 'click', 'stripe')),
  provider_sub_id text,
  card_token text,                 -- payme/click saved card (recurring billing)
  plan text check (plan in ('talaba', 'pro', 'team')),
  status text check (
    status in ('active', 'past_due', 'cancelled', 'cancel_at_period_end')
  ),
  current_period_end timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Payment ledger. amount_uzs is integer UZS (NOT tiyin) — the Payme handler converts
-- incoming tiyin (amount/100) before writing here. state mirrors the Payme convention:
-- 1=created, 2=performed, -1=cancelled-during-init, -2=cancelled.
create table if not exists public.payment_transactions (
  id bigserial primary key,
  user_id uuid references public.users(id) on delete cascade,
  provider text not null,
  provider_tx_id text not null,
  amount_uzs bigint,
  amount_usd numeric,
  state int,
  raw jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists subscriptions_user_idx
  on public.subscriptions (user_id, created_at desc);

-- One row per (provider, provider_tx_id) so webhook retries upsert idempotently.
create unique index if not exists payment_transactions_provider_tx_idx
  on public.payment_transactions (provider, provider_tx_id);

create index if not exists payment_transactions_user_idx
  on public.payment_transactions (user_id, created_at desc);

alter table public.subscriptions enable row level security;
alter table public.payment_transactions enable row level security;

-- Defense-in-depth: webhooks + the billing router use the service-role asyncpg
-- connection (bypasses RLS) and filter by user_id explicitly, like every other router.
-- These policies protect any direct PostgREST access from the browser (read-only is all
-- the web app ever needs; mutations happen server-side).
drop policy if exists subscriptions_self on public.subscriptions;
create policy subscriptions_self on public.subscriptions
  for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

drop policy if exists payment_transactions_self on public.payment_transactions;
create policy payment_transactions_self on public.payment_transactions
  for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);
