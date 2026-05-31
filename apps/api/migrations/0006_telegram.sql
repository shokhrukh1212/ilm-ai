-- Phase 6: Telegram account links (one-time link code + chat binding) with per-user RLS
create table if not exists public.telegram_links (
  id bigserial primary key,
  user_id uuid references public.users(id) on delete cascade,
  telegram_chat_id bigint unique,
  one_time_code text,
  lang text,
  linked_at timestamptz,
  opt_in_daily boolean not null default true,
  created_at timestamptz not null default now()
);

create index if not exists telegram_links_user_idx
  on public.telegram_links (user_id);

create index if not exists telegram_links_code_idx
  on public.telegram_links (one_time_code);

alter table public.telegram_links enable row level security;

-- Defense-in-depth: the bot + link router use the service-role asyncpg connection
-- (bypasses RLS) and filter by user_id explicitly, like every other router. This
-- policy protects any direct PostgREST access from the browser.
drop policy if exists telegram_links_self on public.telegram_links;
create policy telegram_links_self on public.telegram_links
  for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);
