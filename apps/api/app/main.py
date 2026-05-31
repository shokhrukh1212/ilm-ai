import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

import stripe
from fastapi import FastAPI, Header, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from telegram import Update

from .routers import (
    billing,
    chat,
    gaps,
    materials,
    me,
    plan,
    quiz,
    telegram_link,
    webhooks_click,
    webhooks_payme,
    webhooks_stripe,
)
from .settings import settings

if settings.stripe_secret_key:
    stripe.api_key = settings.stripe_secret_key
from .telegram.bot import build_application
from .telegram.scheduler import send_daily_push, start_scheduler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Start the Telegram bot (webhook mode) + daily scheduler alongside the API.

    Skipped entirely in test mode or when no bot token is configured, so the
    sandbox and unit tests never touch the network.
    """
    app.state.telegram_app = None
    app.state.scheduler = None

    if not settings.is_test_mode and settings.telegram_bot_token:
        application = build_application()
        await application.initialize()
        await application.start()
        webhook_url = (
            f"{settings.app_base_url}/webhooks/telegram/{settings.telegram_webhook_secret}"
        )
        await application.bot.set_webhook(
            url=webhook_url,
            secret_token=settings.telegram_webhook_secret,
            allowed_updates=["message", "callback_query"],
        )
        app.state.telegram_app = application
        app.state.scheduler = start_scheduler(application.bot)
        logger.info("Telegram bot started; webhook set to %s", webhook_url)

    try:
        yield
    finally:
        if app.state.scheduler is not None:
            app.state.scheduler.shutdown(wait=False)
        if app.state.telegram_app is not None:
            await app.state.telegram_app.stop()
            await app.state.telegram_app.shutdown()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

_cors_origins = (
    ["*"]
    if settings.is_test_mode
    else [
        settings.frontend_url,
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=not settings.is_test_mode,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(me.router)
app.include_router(materials.router)
app.include_router(chat.router)
app.include_router(quiz.router)
app.include_router(gaps.router)
app.include_router(plan.router)
app.include_router(telegram_link.router)
app.include_router(billing.router)
app.include_router(webhooks_payme.router)
app.include_router(webhooks_click.router)
app.include_router(webhooks_stripe.router)


@app.get("/health")
async def health() -> dict[str, bool]:
    return {"ok": True}


@app.post("/webhooks/telegram/{secret}")
async def telegram_webhook(
    secret: str,
    request: Request,
    x_telegram_bot_api_secret_token: Annotated[str | None, Header()] = None,
) -> Response:
    # Verify both the path secret and the header Telegram echoes back.
    if (
        secret != settings.telegram_webhook_secret
        or x_telegram_bot_api_secret_token != settings.telegram_webhook_secret
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    application = request.app.state.telegram_app
    if application is None:
        # Bot not configured (e.g. test mode) — acknowledge without processing.
        return Response(status_code=status.HTTP_200_OK)

    update = Update.de_json(await request.json(), application.bot)
    await application.process_update(update)
    return Response(status_code=status.HTTP_200_OK)


@app.post("/debug/telegram/push")
async def debug_telegram_push() -> dict[str, bool]:
    """Test-only: trigger the daily push once. Remove or secure for production."""
    application = app.state.telegram_app
    if application is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram bot not configured",
        )
    await send_daily_push(application.bot)
    return {"ok": True}
