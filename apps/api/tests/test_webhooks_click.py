import asyncio
import hashlib
from unittest.mock import AsyncMock

import pytest

from app.routers import webhooks_click as wh
from app.services import billing
from app.settings import settings

USER_ID = "00000000-0000-0000-0000-000000000001"
SECRET = "test-secret"


def _prepare_sign(ct: str, svc: str, mt: str, amt: str, act: str, st: str) -> str:
    return hashlib.md5(f"{ct}{svc}{SECRET}{mt}{amt}{act}{st}".encode()).hexdigest()


def _complete_sign(
    ct: str, svc: str, mt: str, mp: str, amt: str, act: str, st: str
) -> str:
    return hashlib.md5(f"{ct}{svc}{SECRET}{mt}{mp}{amt}{act}{st}".encode()).hexdigest()


@pytest.fixture(autouse=True)
def _secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "click_secret_key", SECRET)


def test_invalid_sign_returns_error_minus_1_no_db_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = AsyncMock()
    user_exists = AsyncMock(return_value=True)
    monkeypatch.setattr(billing, "record_transaction", record)
    monkeypatch.setattr(billing, "user_exists", user_exists)

    res = asyncio.run(
        wh.prepare(
            click_trans_id="111",
            service_id="svc",
            merchant_trans_id=USER_ID,
            amount="29000",
            action="0",
            sign_time="2026-05-31 10:00:00",
            sign_string="deadbeef",  # wrong
        )
    )

    assert res["error"] == wh.ERR_SIGN_CHECK_FAILED
    record.assert_not_awaited()
    user_exists.assert_not_awaited()


def test_prepare_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(billing, "record_transaction", AsyncMock())
    monkeypatch.setattr(billing, "user_exists", AsyncMock(return_value=True))

    sign = _prepare_sign("111", "svc", USER_ID, "29000", "0", "t")
    res = asyncio.run(
        wh.prepare(
            click_trans_id="111",
            service_id="svc",
            merchant_trans_id=USER_ID,
            amount="29000",
            action="0",
            sign_time="t",
            sign_string=sign,
        )
    )

    assert res["error"] == wh.SUCCESS
    assert res["merchant_prepare_id"] == 111


def test_prepare_wrong_amount(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(billing, "record_transaction", AsyncMock())
    monkeypatch.setattr(billing, "user_exists", AsyncMock(return_value=True))

    sign = _prepare_sign("111", "svc", USER_ID, "5000", "0", "t")
    res = asyncio.run(
        wh.prepare(
            click_trans_id="111",
            service_id="svc",
            merchant_trans_id=USER_ID,
            amount="5000",
            action="0",
            sign_time="t",
            sign_string=sign,
        )
    )
    assert res["error"] == wh.ERR_INCORRECT_AMOUNT


def test_complete_activates_talaba(monkeypatch: pytest.MonkeyPatch) -> None:
    activate = AsyncMock()
    monkeypatch.setattr(billing, "activate_subscription", activate)
    monkeypatch.setattr(billing, "record_transaction", AsyncMock())

    sign = _complete_sign("111", "svc", USER_ID, "111", "29000", "1", "t")
    res = asyncio.run(
        wh.complete(
            click_trans_id="111",
            service_id="svc",
            merchant_trans_id=USER_ID,
            merchant_prepare_id="111",
            amount="29000",
            action="1",
            sign_time="t",
            sign_string=sign,
        )
    )

    assert res["error"] == wh.SUCCESS
    activate.assert_awaited_once_with(USER_ID, provider="click", plan="talaba")
