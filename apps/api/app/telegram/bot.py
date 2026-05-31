"""PTB v21 Application factory (webhook mode).

The Application is built in the FastAPI lifespan and shares the process. An
``AIORateLimiter`` throttles outbound messages to Telegram's limits (~30 msg/s)
and transparently retries on ``RetryAfter`` (429) responses — this is the bot's
rate-limit handling, relevant to the daily broadcast.
"""

from typing import Any

from telegram.ext import (
    AIORateLimiter,
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
)

from ..settings import settings
from . import handlers

# Application is generic over (bot, context, user_data, chat_data, bot_data, job_queue).
BotApplication = Application[Any, Any, Any, Any, Any, Any]


def register_handlers(application: BotApplication) -> None:
    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(CommandHandler("link", handlers.link))
    application.add_handler(CommandHandler("help", handlers.help_cmd))
    application.add_handler(CommandHandler("lang", handlers.lang_cmd))
    application.add_handler(CommandHandler("today", handlers.today_cmd))
    application.add_handler(CommandHandler("streak", handlers.streak_cmd))
    application.add_handler(CommandHandler("quiz", handlers.quiz_cmd))
    application.add_handler(CallbackQueryHandler(handlers.quiz_callback, pattern=r"^q:"))


def build_application() -> BotApplication:
    application = (
        ApplicationBuilder()
        .token(settings.telegram_bot_token)
        .rate_limiter(AIORateLimiter())
        .build()
    )
    register_handlers(application)
    return application
