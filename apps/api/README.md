# Ilm AI API

FastAPI backend for Ilm AI. Phase 0 exposes `/health`; feature routers are added in later phases.

## Telegram bot (Phase 6) — local development with ngrok

The bot runs **in webhook mode inside this FastAPI process** (built in the app
lifespan). It is **disabled** whenever `IS_TEST_MODE=True` or `TELEGRAM_BOT_TOKEN`
is empty, so the default dev/test setup never touches Telegram.

To exercise the bot locally you need a public HTTPS URL that Telegram can reach:

1. Create a bot with [@BotFather](https://t.me/BotFather); copy the token and the
   bot username.
2. Start a tunnel to the API port:
   ```bash
   ngrok http 8000
   ```
   Copy the `https://….ngrok-free.app` URL.
3. In `apps/api/.env` set:
   ```
   IS_TEST_MODE=False
   APP_BASE_URL=https://<your-ngrok-subdomain>.ngrok-free.app
   TELEGRAM_BOT_TOKEN=<token from BotFather>
   TELEGRAM_WEBHOOK_SECRET=<random 32+ char string>
   TELEGRAM_BOT_USERNAME=<bot username without @>
   ```
   Also set `FRONTEND_URL` so the bot's "open plan" buttons link to your web app.
4. Start the API:
   ```bash
   uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
   On startup the lifespan calls `setWebhook` to
   `{APP_BASE_URL}/webhooks/telegram/{TELEGRAM_WEBHOOK_SECRET}` with a secret
   token. Telegram echoes that token in the `X-Telegram-Bot-Api-Secret-Token`
   header on every update, and the webhook route rejects any mismatch.
5. Message the bot: `/start`, then link via the web `/telegram` page
   (`/link CODE` or the `t.me/<bot>?start=CODE` deep link), then try `/quiz`,
   `/today`, `/streak`.

### Daily push

A daily learning-plan broadcast fires at `TELEGRAM_DAILY_PUSH_HOUR` (default 9)
in `TELEGRAM_TZ` (default `Asia/Tashkent`) to every opt-in linked learner. To
trigger it once for testing:

```bash
curl -X POST http://localhost:8000/debug/telegram/push
```

> `/debug/telegram/push` is unauthenticated and intended for local testing only —
> remove or secure it before production.
