"""Telegram command + callback handlers.

Handlers stay thin: all DB access goes through ``services.telegram_service`` and
all user-facing copy through ``strings.t``. Every handler is wrapped so an
exception is logged and turned into a soft error reply, never a crash.
"""

import asyncio
import functools
import logging
from collections.abc import Callable, Coroutine
from typing import Any

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes

from ..agents.quiz_gen import QuizProvider
from ..services import telegram_service as svc
from ..services.gap_detection import run_gap_detection
from ..services.quiz_session import QuizSourcesEmpty, create_quiz_session
from ..settings import settings
from .strings import t

logger = logging.getLogger(__name__)

QUIZ_NUM_QUESTIONS = 3
QUIZ_DIFFICULTY = "medium"
QUIZ_PROVIDER: QuizProvider = "anthropic"  # only the Anthropic key is configured for the bot
QUIZ_TIMEOUT_S = 25.0

Handler = Callable[[Update, ContextTypes.DEFAULT_TYPE], Coroutine[Any, Any, None]]


def _chat_id(update: Update) -> int | None:
    return update.effective_chat.id if update.effective_chat else None


def guard(handler: Handler) -> Handler:
    """Wrap a handler so failures log and reply softly instead of crashing."""

    @functools.wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        try:
            await handler(update, context)
        except Exception:
            logger.exception("telegram handler %s failed", handler.__name__)
            chat_id = _chat_id(update)
            if chat_id is not None and context.bot is not None:
                lang = await _safe_lang(chat_id)
                await context.bot.send_message(chat_id, t(lang, "error"))

    return wrapper


async def _safe_lang(chat_id: int) -> str:
    try:
        return await svc.resolve_lang(chat_id)
    except Exception:
        return svc.DEFAULT_LANG


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

@guard
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = _chat_id(update)
    if chat_id is None or update.message is None:
        return
    # Deep-link: /start CODE auto-links the account.
    if context.args:
        await _try_link(update, context, context.args[0])
        return
    user = await svc.user_by_chat(chat_id)
    if user:
        await update.message.reply_text(t(user["lang"], "greet_linked"))
    else:
        await update.message.reply_text(t(svc.DEFAULT_LANG, "greet"))


@guard
async def link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = _chat_id(update)
    if chat_id is None or update.message is None:
        return
    lang = await svc.resolve_lang(chat_id)
    if not context.args:
        await update.message.reply_text(t(lang, "link_usage"))
        return
    await _try_link(update, context, context.args[0])


async def _try_link(
    update: Update, context: ContextTypes.DEFAULT_TYPE, code: str
) -> None:
    chat_id = _chat_id(update)
    if chat_id is None or update.message is None:
        return
    result = await svc.redeem_code(chat_id, code)
    if result is None:
        lang = await svc.resolve_lang(chat_id)
        await update.message.reply_text(t(lang, "link_invalid"))
        return
    await update.message.reply_text(
        t(result["lang"], "linked", email=result["email"] or "")
    )


@guard
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = _chat_id(update)
    if chat_id is None or update.message is None:
        return
    lang = await svc.resolve_lang(chat_id)
    await update.message.reply_text(t(lang, "help"))


@guard
async def lang_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = _chat_id(update)
    if chat_id is None or update.message is None:
        return
    current = await svc.resolve_lang(chat_id)
    if not context.args:
        await update.message.reply_text(t(current, "lang_usage"))
        return
    new_lang = svc.normalize_lang(context.args[0])
    if new_lang is None:
        await update.message.reply_text(t(current, "lang_usage"))
        return
    ok = await svc.set_lang(chat_id, new_lang)
    if not ok:
        await update.message.reply_text(t(current, "lang_not_linked"))
        return
    await update.message.reply_text(t(new_lang, "lang_set"))


@guard
async def today_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = _chat_id(update)
    if chat_id is None or update.message is None:
        return
    user = await svc.user_by_chat(chat_id)
    if user is None:
        await update.message.reply_text(t(svc.DEFAULT_LANG, "need_link"))
        return
    lang = user["lang"]
    tasks = await svc.today_tasks(user["user_id"])
    if not tasks:
        await update.message.reply_text(t(lang, "today_empty"))
        return
    lines = [t(lang, "today_header")]
    for task in tasks:
        mark = "✅" if task.get("done") else "▫️"
        minutes = task.get("estimated_minutes")
        suffix = f" ({minutes} min)" if minutes else ""
        lines.append(f"{mark} {task.get('title', '')}{suffix}")
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(t(lang, "today_btn"), url=f"{settings.frontend_url}/plan")]]
    )
    await update.message.reply_text("\n".join(lines), reply_markup=keyboard)


@guard
async def streak_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = _chat_id(update)
    if chat_id is None or update.message is None:
        return
    user = await svc.user_by_chat(chat_id)
    if user is None:
        await update.message.reply_text(t(svc.DEFAULT_LANG, "need_link"))
        return
    lang = user["lang"]
    n = await svc.streak(user["user_id"])
    await update.message.reply_text(
        t(lang, "streak", n=n) if n > 0 else t(lang, "streak_zero")
    )


@guard
async def quiz_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = _chat_id(update)
    if chat_id is None or update.message is None:
        return
    user = await svc.user_by_chat(chat_id)
    if user is None:
        await update.message.reply_text(t(svc.DEFAULT_LANG, "need_link"))
        return
    lang = user["lang"]
    material_id = await svc.latest_ready_material(user["user_id"])
    if material_id is None:
        await update.message.reply_text(t(lang, "quiz_no_material"))
        return

    try:
        _session_id, questions = await create_quiz_session(
            user_id=user["user_id"],
            material_id=material_id,
            num_questions=QUIZ_NUM_QUESTIONS,
            difficulty=QUIZ_DIFFICULTY,
            lang=lang,
            provider=QUIZ_PROVIDER,
            timeout_s=QUIZ_TIMEOUT_S,
        )
    except (QuizSourcesEmpty, asyncio.TimeoutError):
        await update.message.reply_text(t(lang, "quiz_no_material"))
        return

    # Send the first MCQ (skip any open-ended questions — no inline UI for those).
    first = next((q for q in questions if q.type == "mcq" and q.options), None)
    if first is None:
        await update.message.reply_text(t(lang, "quiz_no_material"))
        return
    await update.message.reply_text(t(lang, "quiz_intro"))
    await _send_question(
        context, chat_id, first.id, first.prompt, first.options or []
    )


# ---------------------------------------------------------------------------
# Inline quiz callback
# ---------------------------------------------------------------------------

async def _send_question(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    question_id: int,
    prompt: str,
    options: list[str],
) -> None:
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(opt, callback_data=f"q:{question_id}:{idx}")]
            for idx, opt in enumerate(options)
        ]
    )
    await context.bot.send_message(chat_id, prompt, reply_markup=keyboard)


@guard
async def quiz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    chat_id = _chat_id(update)
    if query is None or chat_id is None or not query.data:
        return
    await query.answer()

    try:
        _, qid_raw, idx_raw = query.data.split(":")
        question_id = int(qid_raw)
        choice_idx = int(idx_raw)
    except (ValueError, IndexError):
        return

    user = await svc.user_by_chat(chat_id)
    if user is None:
        await query.edit_message_text(t(svc.DEFAULT_LANG, "need_link"))
        return
    lang = user["lang"]

    question = await svc.quiz_question_for_user(question_id, user["user_id"])
    if question is None:
        await query.edit_message_text(t(lang, "error"))
        return

    options = question["options"] or []
    if choice_idx >= len(options):
        return
    selected = options[choice_idx]
    correct_answer = question["correct_answer"]
    is_correct = selected.strip() == correct_answer.strip()

    await svc.record_answer(question_id, selected, is_correct)

    if is_correct:
        result = t(lang, "quiz_correct", rationale=question["rationale"])
    else:
        result = t(
            lang, "quiz_wrong", correct=correct_answer, rationale=question["rationale"]
        )
    await query.edit_message_text(f"{question['prompt']}\n\n{result}")

    # Advance to the next unanswered MCQ, or finish the session.
    session_id = question["session_id"]
    nxt = await svc.next_question(session_id, user["user_id"])
    while nxt is not None and (nxt["type"] != "mcq" or not nxt["options"]):
        # Auto-skip open questions the inline UI can't present.
        await svc.record_answer(int(nxt["id"]), "", False)
        nxt = await svc.next_question(session_id, user["user_id"])

    if nxt is None:
        correct_count, total = await svc.session_progress(session_id)
        await context.bot.send_message(
            chat_id, t(lang, "quiz_done", correct=correct_count, total=total)
        )
        # Refresh knowledge gaps from the updated history (fire-and-forget).
        asyncio.create_task(run_gap_detection(user["user_id"]))
    else:
        await _send_question(
            context, chat_id, int(nxt["id"]), nxt["prompt"], nxt["options"] or []
        )
