-- Phase 3: chat sessions and messages with per-user RLS
create table if not exists public.chat_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  material_ids uuid[] not null default '{}',
  title text,
  created_at timestamptz not null default now()
);

create table if not exists public.chat_messages (
  id bigserial primary key,
  session_id uuid not null references public.chat_sessions(id) on delete cascade,
  role text not null check (role in ('user', 'assistant', 'system')),
  content text not null,
  citations jsonb,
  tokens_in int,
  tokens_out int,
  model text,
  latency_ms int,
  prompt_variant text,
  created_at timestamptz not null default now()
);

create index if not exists chat_sessions_user_created_idx
  on public.chat_sessions (user_id, created_at desc);

create index if not exists chat_messages_session_created_idx
  on public.chat_messages (session_id, created_at);

alter table public.chat_sessions enable row level security;
alter table public.chat_messages enable row level security;

drop policy if exists chat_sessions_self on public.chat_sessions;
create policy chat_sessions_self on public.chat_sessions
  for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

drop policy if exists chat_messages_self on public.chat_messages;
create policy chat_messages_self on public.chat_messages
  for all
  using (
    session_id in (
      select id from public.chat_sessions where user_id = auth.uid()
    )
  )
  with check (
    session_id in (
      select id from public.chat_sessions where user_id = auth.uid()
    )
  );
