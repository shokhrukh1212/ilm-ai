import asyncio
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException

from app import main
from app.settings import settings

SECRET = "secret123"


def _fake_request(telegram_app: object | None) -> Any:
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(telegram_app=telegram_app)))


class TestWebhookSecurity:
    def test_path_secret_mismatch_rejected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(settings, "telegram_webhook_secret", SECRET)
        with pytest.raises(HTTPException) as exc:
            asyncio.run(main.telegram_webhook("wrong", _fake_request(None), SECRET))
        assert exc.value.status_code == 403

    def test_header_mismatch_rejected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(settings, "telegram_webhook_secret", SECRET)
        with pytest.raises(HTTPException) as exc:
            asyncio.run(main.telegram_webhook(SECRET, _fake_request(None), "wrong"))
        assert exc.value.status_code == 403

    def test_noop_when_bot_unconfigured(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(settings, "telegram_webhook_secret", SECRET)
        response = asyncio.run(main.telegram_webhook(SECRET, _fake_request(None), SECRET))
        assert response.status_code == 200
