from pathlib import Path


def test_chat_migration_has_expected_tables_and_rls() -> None:
    sql = Path("migrations/0003_chat.sql").read_text()

    assert "create table if not exists public.chat_sessions" in sql
    assert "create table if not exists public.chat_messages" in sql
    assert "references public.chat_sessions(id) on delete cascade" in sql
    assert "alter table public.chat_sessions enable row level security" in sql
    assert "alter table public.chat_messages enable row level security" in sql
    assert "create policy chat_sessions_self" in sql
    assert "create policy chat_messages_self" in sql
    assert "chat_sessions_user_created_idx" in sql
    assert "chat_messages_session_created_idx" in sql
