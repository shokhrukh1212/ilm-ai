"""Database layer for the Telegram bot and the web link router.

All access uses the service-role asyncpg connection (``db.connect``), which
bypasses RLS, so every query filters by ``user_id``/``telegram_chat_id``
explicitly — the same pattern every other router in this app follows.
"""

import json
import secrets
from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from .. import db
from ..settings import settings

DEFAULT_LANG = "uz-latn"
VALID_LANGS = {"uz-latn", "uz-cyrl", "ru", "en"}
# Short bot-friendly lang aliases accepted by /lang.
LANG_ALIASES = {
    "uz": "uz-latn",
    "uzc": "uz-cyrl",
    "uz-cyrl": "uz-cyrl",
    "uz-latn": "uz-latn",
    "ru": "ru",
    "en": "en",
}


def _tz() -> ZoneInfo:
    return ZoneInfo(settings.telegram_tz)


def today_local() -> date:
    return datetime.now(_tz()).date()


def generate_code() -> str:
    """A short, human-typable one-time code (8 hex chars, upper-cased)."""
    return secrets.token_hex(4).upper()


def normalize_lang(raw: str) -> str | None:
    return LANG_ALIASES.get(raw.strip().lower())


# ---------------------------------------------------------------------------
# Web link router helpers (user-scoped, JWT-authenticated callers)
# ---------------------------------------------------------------------------

async def create_link_code(user_id: str) -> str:
    """Issue a fresh one-time code, dropping the user's prior unlinked rows."""
    code = generate_code()
    connection = await db.connect()
    try:
        async with connection.transaction():
            await connection.execute(
                """
                DELETE FROM public.telegram_links
                WHERE user_id = $1::uuid AND telegram_chat_id IS NULL
                """,
                user_id,
            )
            await connection.execute(
                """
                INSERT INTO public.telegram_links (user_id, one_time_code)
                VALUES ($1::uuid, $2)
                """,
                user_id,
                code,
            )
    finally:
        await connection.close()
    return code


async def link_status(user_id: str) -> dict[str, bool]:
    connection = await db.connect()
    try:
        row = await connection.fetchrow(
            """
            SELECT telegram_chat_id, opt_in_daily
            FROM public.telegram_links
            WHERE user_id = $1::uuid AND telegram_chat_id IS NOT NULL
            ORDER BY linked_at DESC NULLS LAST
            LIMIT 1
            """,
            user_id,
        )
    finally:
        await connection.close()
    if row is None:
        return {"linked": False, "opt_in_daily": True}
    return {"linked": True, "opt_in_daily": bool(row["opt_in_daily"])}


async def set_opt_in(user_id: str, opt_in: bool) -> dict[str, bool]:
    connection = await db.connect()
    try:
        await connection.execute(
            """
            UPDATE public.telegram_links
            SET opt_in_daily = $2
            WHERE user_id = $1::uuid AND telegram_chat_id IS NOT NULL
            """,
            user_id,
            opt_in,
        )
    finally:
        await connection.close()
    return await link_status(user_id)


# ---------------------------------------------------------------------------
# Bot helpers (chat-scoped)
# ---------------------------------------------------------------------------

async def redeem_code(chat_id: int, code: str) -> dict[str, Any] | None:
    """Bind a chat to the user who generated ``code``.

    Returns ``{"email", "lang"}`` on success, or ``None`` if the code is
    unknown / already used.
    """
    normalized = code.strip().upper()
    connection = await db.connect()
    try:
        async with connection.transaction():
            row = await connection.fetchrow(
                """
                SELECT id, user_id::text AS user_id
                FROM public.telegram_links
                WHERE one_time_code = $1
                  AND telegram_chat_id IS NULL
                  AND linked_at IS NULL
                FOR UPDATE
                """,
                normalized,
            )
            if row is None:
                return None
            # Respect the unique(telegram_chat_id) constraint: drop any prior
            # link for this chat before binding the new one.
            await connection.execute(
                "DELETE FROM public.telegram_links WHERE telegram_chat_id = $1",
                chat_id,
            )
            await connection.execute(
                """
                UPDATE public.telegram_links
                SET telegram_chat_id = $2, linked_at = now(), one_time_code = NULL
                WHERE id = $1
                """,
                row["id"],
                chat_id,
            )
            user = await connection.fetchrow(
                "SELECT email, lang FROM public.users WHERE id = $1::uuid",
                row["user_id"],
            )
    finally:
        await connection.close()
    return {
        "email": user["email"] if user else None,
        "lang": (user["lang"] if user else None) or DEFAULT_LANG,
    }


async def user_by_chat(chat_id: int) -> dict[str, Any] | None:
    connection = await db.connect()
    try:
        row = await connection.fetchrow(
            """
            SELECT t.user_id::text AS user_id, t.lang AS link_lang,
                   u.email, u.lang AS user_lang
            FROM public.telegram_links t
            JOIN public.users u ON u.id = t.user_id
            WHERE t.telegram_chat_id = $1
            """,
            chat_id,
        )
    finally:
        await connection.close()
    if row is None:
        return None
    return {
        "user_id": row["user_id"],
        "email": row["email"],
        "lang": row["link_lang"] or row["user_lang"] or DEFAULT_LANG,
    }


async def resolve_lang(chat_id: int) -> str:
    user = await user_by_chat(chat_id)
    return user["lang"] if user else DEFAULT_LANG


async def set_lang(chat_id: int, lang: str) -> bool:
    """Persist a chat's language. Returns False if the chat isn't linked."""
    connection = await db.connect()
    try:
        result = await connection.execute(
            "UPDATE public.telegram_links SET lang = $2 WHERE telegram_chat_id = $1",
            chat_id,
            lang,
        )
    finally:
        await connection.close()
    # asyncpg returns e.g. "UPDATE 1"
    return bool(result.rsplit(" ", 1)[-1] != "0")


async def latest_ready_material(user_id: str) -> str | None:
    connection = await db.connect()
    try:
        row = await connection.fetchrow(
            """
            SELECT id::text FROM public.materials
            WHERE user_id = $1::uuid AND status = 'ready'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            user_id,
        )
    finally:
        await connection.close()
    return row["id"] if row else None


async def today_tasks(user_id: str) -> list[dict[str, Any]]:
    """Tasks scheduled for today (Asia/Tashkent) in the learner's latest plan."""
    connection = await db.connect()
    try:
        row = await connection.fetchrow(
            """
            SELECT plan FROM public.learning_plans
            WHERE user_id = $1::uuid
            ORDER BY created_at DESC
            LIMIT 1
            """,
            user_id,
        )
    finally:
        await connection.close()
    if row is None:
        return []
    today = today_local().isoformat()
    for day in _parse_plan_days(row["plan"]):
        if day.get("date") == today:
            return list(day.get("tasks", []))
    return []


async def streak(user_id: str) -> int:
    """Consecutive calendar days (Asia/Tashkent) with >=1 quiz answer.

    Counts back from today; if there's no activity today the streak may still
    be anchored on yesterday (so an active streak isn't lost mid-day).
    """
    connection = await db.connect()
    try:
        rows = await connection.fetch(
            """
            SELECT DISTINCT (a.created_at AT TIME ZONE $2)::date AS d
            FROM public.quiz_answers a
            JOIN public.quiz_questions q ON q.id = a.question_id
            JOIN public.quiz_sessions s ON s.id = q.session_id
            WHERE s.user_id = $1::uuid
            ORDER BY d DESC
            """,
            user_id,
            settings.telegram_tz,
        )
    finally:
        await connection.close()
    active_days = {r["d"] for r in rows}
    if not active_days:
        return 0
    today = today_local()
    cursor = today if today in active_days else today - timedelta(days=1)
    count = 0
    while cursor in active_days:
        count += 1
        cursor -= timedelta(days=1)
    return count


async def optin_users() -> list[dict[str, Any]]:
    connection = await db.connect()
    try:
        rows = await connection.fetch(
            """
            SELECT telegram_chat_id, user_id::text AS user_id,
                   coalesce(t.lang, u.lang, $1) AS lang
            FROM public.telegram_links t
            JOIN public.users u ON u.id = t.user_id
            WHERE t.telegram_chat_id IS NOT NULL AND t.opt_in_daily = true
            """,
            DEFAULT_LANG,
        )
    finally:
        await connection.close()
    return [
        {
            "chat_id": int(r["telegram_chat_id"]),
            "user_id": r["user_id"],
            "lang": r["lang"] or DEFAULT_LANG,
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# In-bot quiz answering
# ---------------------------------------------------------------------------

async def quiz_question_for_user(question_id: int, user_id: str) -> dict[str, Any] | None:
    """Load a question and verify the chat's user owns its session."""
    connection = await db.connect()
    try:
        row = await connection.fetchrow(
            """
            SELECT q.id, q.session_id::text AS session_id, q.options,
                   q.correct_answer, q.rationale
            FROM public.quiz_questions q
            JOIN public.quiz_sessions s ON s.id = q.session_id
            WHERE q.id = $1::bigint AND s.user_id = $2::uuid
            """,
            question_id,
            user_id,
        )
    finally:
        await connection.close()
    if row is None:
        return None
    return {
        "id": int(row["id"]),
        "session_id": row["session_id"],
        "options": _parse_options(row["options"]),
        "correct_answer": row["correct_answer"] or "",
        "rationale": row["rationale"] or "",
    }


async def record_answer(question_id: int, user_answer: str, is_correct: bool) -> None:
    connection = await db.connect()
    try:
        async with connection.transaction():
            await connection.execute(
                "DELETE FROM public.quiz_answers WHERE question_id = $1::bigint",
                question_id,
            )
            await connection.execute(
                """
                INSERT INTO public.quiz_answers
                  (question_id, user_answer, is_correct, ai_feedback)
                VALUES ($1::bigint, $2, $3, '')
                """,
                question_id,
                user_answer,
                is_correct,
            )
    finally:
        await connection.close()


async def next_question(session_id: str, user_id: str) -> dict[str, Any] | None:
    """The next unanswered question in a session (by order), or None if done."""
    connection = await db.connect()
    try:
        row = await connection.fetchrow(
            """
            SELECT q.id, q.type, q.prompt, q.options
            FROM public.quiz_questions q
            JOIN public.quiz_sessions s ON s.id = q.session_id
            WHERE q.session_id = $1::uuid AND s.user_id = $2::uuid
              AND NOT EXISTS (
                SELECT 1 FROM public.quiz_answers a WHERE a.question_id = q.id
              )
            ORDER BY q.ord ASC
            LIMIT 1
            """,
            session_id,
            user_id,
        )
    finally:
        await connection.close()
    if row is None:
        return None
    return {
        "id": int(row["id"]),
        "type": row["type"],
        "prompt": row["prompt"],
        "options": _parse_options(row["options"]),
    }


async def session_progress(session_id: str) -> tuple[int, int]:
    """(correct_count, total_questions) for a session."""
    connection = await db.connect()
    try:
        total = await connection.fetchval(
            "SELECT count(*) FROM public.quiz_questions WHERE session_id = $1::uuid",
            session_id,
        )
        correct = await connection.fetchval(
            """
            SELECT count(*)
            FROM public.quiz_answers a
            JOIN public.quiz_questions q ON q.id = a.question_id
            WHERE q.session_id = $1::uuid AND a.is_correct = true
            """,
            session_id,
        )
    finally:
        await connection.close()
    return int(correct or 0), int(total or 0)


# ---------------------------------------------------------------------------
# Pure helpers (unit-tested)
# ---------------------------------------------------------------------------

def _parse_options(raw: Any) -> list[str] | None:
    if raw is None:
        return None
    if isinstance(raw, str):
        parsed = json.loads(raw)
        return list(parsed) if parsed is not None else None
    return list(raw)

def _parse_plan_days(raw: Any) -> list[dict[str, Any]]:
    if raw is None:
        return []
    if isinstance(raw, str):
        raw = json.loads(raw)
    if isinstance(raw, dict):
        return list(raw.get("plan", []))
    return list(raw)
