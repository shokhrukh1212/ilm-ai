-- Phase 4: quiz sessions, questions, and answers with per-user RLS
create table if not exists public.quiz_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  material_id uuid not null references public.materials(id) on delete cascade,
  lang text,
  difficulty text check (difficulty in ('easy', 'medium', 'hard')),
  num_questions int,
  score numeric,
  started_at timestamptz not null default now(),
  completed_at timestamptz
);

create table if not exists public.quiz_questions (
  id bigserial primary key,
  session_id uuid not null references public.quiz_sessions(id) on delete cascade,
  type text not null check (type in ('mcq', 'open')),
  prompt text not null,
  options jsonb,
  correct_answer text,
  rationale text,
  source_chunk_ids bigint[],
  ord int not null default 0
);

create table if not exists public.quiz_answers (
  id bigserial primary key,
  question_id bigint not null references public.quiz_questions(id) on delete cascade,
  user_answer text,
  is_correct boolean,
  ai_feedback text,
  time_spent_s int,
  created_at timestamptz not null default now()
);

create index if not exists quiz_sessions_user_started_idx
  on public.quiz_sessions (user_id, started_at desc);

create index if not exists quiz_questions_session_ord_idx
  on public.quiz_questions (session_id, ord);

create index if not exists quiz_answers_question_idx
  on public.quiz_answers (question_id);

alter table public.quiz_sessions enable row level security;
alter table public.quiz_questions enable row level security;
alter table public.quiz_answers enable row level security;

drop policy if exists quiz_sessions_self on public.quiz_sessions;
create policy quiz_sessions_self on public.quiz_sessions
  for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

drop policy if exists quiz_questions_self on public.quiz_questions;
create policy quiz_questions_self on public.quiz_questions
  for all
  using (
    session_id in (
      select id from public.quiz_sessions where user_id = auth.uid()
    )
  )
  with check (
    session_id in (
      select id from public.quiz_sessions where user_id = auth.uid()
    )
  );

drop policy if exists quiz_answers_self on public.quiz_answers;
create policy quiz_answers_self on public.quiz_answers
  for all
  using (
    question_id in (
      select q.id
      from public.quiz_questions q
      join public.quiz_sessions s on s.id = q.session_id
      where s.user_id = auth.uid()
    )
  )
  with check (
    question_id in (
      select q.id
      from public.quiz_questions q
      join public.quiz_sessions s on s.id = q.session_id
      where s.user_id = auth.uid()
    )
  );
