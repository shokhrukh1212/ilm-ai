from pathlib import Path


def test_telegram_migration_table_and_rls() -> None:
    sql = Path("migrations/0006_telegram.sql").read_text()

    assert "create table if not exists public.telegram_links" in sql
    assert "telegram_chat_id bigint unique" in sql
    assert "one_time_code text" in sql
    assert "opt_in_daily boolean not null default true" in sql

    assert "alter table public.telegram_links enable row level security" in sql
    assert "create policy telegram_links_self" in sql
    assert "auth.uid() = user_id" in sql

    assert "telegram_links_user_idx" in sql
    assert "telegram_links_code_idx" in sql
