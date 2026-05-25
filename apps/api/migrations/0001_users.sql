-- Phase 1: users table mirrors auth.users with profile + tier fields
create table if not exists public.users (
  id uuid primary key references auth.users(id) on delete cascade,
  email text unique not null,
  full_name text,
  lang text check (lang in ('uz-latn','uz-cyrl','ru','en')) default 'uz-latn',
  goal text,
  minutes_per_day int check (minutes_per_day between 5 and 240),
  tier text check (tier in ('free','talaba','pro','team')) default 'free',
  daily_token_budget int default 50000,
  onboarded_at timestamptz,
  created_at timestamptz default now()
);

alter table public.users enable row level security;

create policy users_self on public.users
  for all
  using (auth.uid() = id)
  with check (auth.uid() = id);

-- Auto-create a users row when auth.users row is inserted
create or replace function public.handle_new_auth_user()
returns trigger language plpgsql security definer as $$
begin
  insert into public.users (id, email, full_name)
  values (
    new.id,
    new.email,
    new.raw_user_meta_data->>'full_name'
  )
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_auth_user();
