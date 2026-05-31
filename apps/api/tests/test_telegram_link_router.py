import asyncio
from unittest.mock import AsyncMock

import pytest

from app.routers import telegram_link as router
from app.routers.telegram_link import OptInRequest
from app.services import telegram_service as svc
from app.settings import settings

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"


class TestLinkStart:
    def test_returns_code_and_username(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(svc, "create_link_code", AsyncMock(return_value="ABCD1234"))
        monkeypatch.setattr(settings, "telegram_bot_username", "ilm_ai_bot")
        res = asyncio.run(router.link_start(TEST_USER_ID))
        assert res.code == "ABCD1234"
        assert res.bot_username == "ilm_ai_bot"


class TestLinkStatus:
    def test_maps_service_dict(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            svc,
            "link_status",
            AsyncMock(return_value={"linked": True, "opt_in_daily": False}),
        )
        res = asyncio.run(router.link_status(TEST_USER_ID))
        assert res.linked is True
        assert res.opt_in_daily is False


class TestOptIn:
    def test_passes_flag_to_service(self, monkeypatch: pytest.MonkeyPatch) -> None:
        set_opt_in = AsyncMock(return_value={"linked": True, "opt_in_daily": False})
        monkeypatch.setattr(svc, "set_opt_in", set_opt_in)
        res = asyncio.run(router.link_opt_in(OptInRequest(opt_in=False), TEST_USER_ID))
        set_opt_in.assert_awaited_once_with(TEST_USER_ID, False)
        assert res.opt_in_daily is False
