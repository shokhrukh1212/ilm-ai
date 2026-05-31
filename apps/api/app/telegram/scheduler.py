"""Daily learning-plan push via APScheduler.

Runs in the same FastAPI process as the bot. The job fires once a day at
``TELEGRAM_DAILY_PUSH_HOUR`` (Asia/Tashkent) and messages every opt-in linked
learner. Per-user send errors are caught so one failure can't abort the batch;
the Application's ``AIORateLimiter`` handles throttling.
"""

import logging
from typing import Any
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

from ..services import telegram_service as svc
from ..settings import settings
from .strings import t

logger = logging.getLogger(__name__)


async def send_daily_push(bot: Bot) -> None:
    users = await svc.optin_users()
    plan_url = f"{settings.frontend_url}/plan"
    for user in users:
        try:
            lang = user["lang"]
            tasks = await svc.today_tasks(user["user_id"])
            text = t(lang, "daily_push")
            if tasks:
                pending = sum(1 for task in tasks if not task.get("done"))
                text = f"{text}\n{t(lang, 'today_header')} {pending}/{len(tasks)}"
            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton(t(lang, "today_btn"), url=plan_url)]]
            )
            await bot.send_message(user["chat_id"], text, reply_markup=keyboard)
        except Exception:
            logger.exception(
                "daily push failed chat=%s", user.get("chat_id")
            )


def start_scheduler(bot: Bot) -> Any:
    scheduler = AsyncIOScheduler(timezone=ZoneInfo(settings.telegram_tz))
    scheduler.add_job(
        send_daily_push,
        trigger="cron",
        hour=settings.telegram_daily_push_hour,
        minute=0,
        args=[bot],
        id="daily_plan_push",
        replace_existing=True,
    )
    scheduler.start()
    return scheduler
