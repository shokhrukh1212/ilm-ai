from pathlib import Path


def test_gaps_plans_migration_tables_and_rls() -> None:
    sql = Path("migrations/0005_gaps_plans.sql").read_text()

    assert "create table if not exists public.knowledge_gaps" in sql
    assert "create table if not exists public.learning_plans" in sql

    assert "severity int check (severity between 1 and 5)" in sql
    assert "evidence jsonb" in sql
    assert "status text not null check (status in ('open', 'closed')) default 'open'" in sql
    assert "plan jsonb" in sql

    assert "alter table public.knowledge_gaps enable row level security" in sql
    assert "alter table public.learning_plans enable row level security" in sql
    assert "create policy knowledge_gaps_self" in sql
    assert "create policy learning_plans_self" in sql

    assert "knowledge_gaps_user_status_idx" in sql
    assert "learning_plans_user_created_idx" in sql
