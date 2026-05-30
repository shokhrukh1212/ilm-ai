from pathlib import Path


def test_quiz_migration_has_expected_tables_and_rls() -> None:
    sql = Path("migrations/0004_quiz.sql").read_text()

    assert "create table if not exists public.quiz_sessions" in sql
    assert "create table if not exists public.quiz_questions" in sql
    assert "create table if not exists public.quiz_answers" in sql

    assert "references public.quiz_sessions(id) on delete cascade" in sql
    assert "references public.quiz_questions(id) on delete cascade" in sql

    assert "alter table public.quiz_sessions enable row level security" in sql
    assert "alter table public.quiz_questions enable row level security" in sql
    assert "alter table public.quiz_answers enable row level security" in sql

    assert "create policy quiz_sessions_self" in sql
    assert "create policy quiz_questions_self" in sql
    assert "create policy quiz_answers_self" in sql

    assert "quiz_sessions_user_started_idx" in sql
    assert "quiz_questions_session_ord_idx" in sql
    assert "quiz_answers_question_idx" in sql


def test_quiz_questions_schema_columns() -> None:
    sql = Path("migrations/0004_quiz.sql").read_text()
    assert "type text not null check (type in ('mcq', 'open'))" in sql
    assert "options jsonb" in sql
    assert "source_chunk_ids bigint[]" in sql
    assert "score numeric" in sql
