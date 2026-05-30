-- Phase 5: knowledge gaps and learning plans with per-user RLS
create table if not exists public.knowledge_gaps (
  id bigserial primary key,
  user_id uuid not null references public.users(id) on delete cascade,
  material_id uuid references public.materials(id) on delete cascade,
  topic text not null,
  severity int check (severity between 1 and 5),
  evidence jsonb,
  status text not null check (status in ('open', 'closed')) default 'open',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.learning_plans (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  start_date date,
  end_date date,
  plan jsonb,
  generated_by text,
  created_at timestamptz not null default now()
);

create index if not exists knowledge_gaps_user_status_idx
  on public.knowledge_gaps (user_id, status);

create index if not exists learning_plans_user_created_idx
  on public.learning_plans (user_id, created_at desc);

alter table public.knowledge_gaps enable row level security;
alter table public.learning_plans enable row level security;

drop policy if exists knowledge_gaps_self on public.knowledge_gaps;
create policy knowledge_gaps_self on public.knowledge_gaps
  for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

drop policy if exists learning_plans_self on public.learning_plans;
create policy learning_plans_self on public.learning_plans
  for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);
