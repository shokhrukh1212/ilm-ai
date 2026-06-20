"""Native Click Merchant API webhooks: Prepare (action=0) + Complete (action=1).

Click posts form-encoded callbacks. We verify the MD5 ``sign_string`` BEFORE any DB
write — an invalid signature returns ``error=-1`` with no state change. merchant_trans_id
carries our user id; a successful Complete activates the Talaba tier.

Sign formulas (docs.click.uz):
  Prepare:  md5(click_trans_id + service_id + SECRET_KEY + merchant_trans_id +
                amount + action + sign_time)
  Complete: md5(click_trans_id + service_id + SECRET_KEY + merchant_trans_id +
                merchant_prepare_id + amount + action + sign_time)
"""

import hashlib
import logging
from typing import Annotated, Any

from fastapi import APIRouter, Form

from ..services import billing
from ..settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/click", tags=["webhooks"])

# Click error codes.
SUCCESS = 0
ERR_SIGN_CHECK_FAILED = -1
ERR_INCORRECT_AMOUNT = -2
ERR_ACTION_NOT_FOUND = -3
ERR_USER_NOT_FOUND = -5
ERR_TRANS_CANCELLED = -9

ACTION_PREPARE = "0"
ACTION_COMPLETE = "1"

_PLAN = "talaba"


def _compute_sign(parts: list[str]) -> str:
    return hashlib.md5("".join(parts).encode("utf-8")).hexdigest()


def verify_prepare_sign(
    *,
    click_trans_id: str,
    service_id: str,
    merchant_trans_id: str,
    amount: str,
    action: str,
    sign_time: str,
    sign_string: str,
    secret_key: str,
) -> bool:
    expected = _compute_sign(
        [click_trans_id, service_id, secret_key, merchant_trans_id, amount, action, sign_time]
    )
    return expected == sign_string


def verify_complete_sign(
    *,
    click_trans_id: str,
    service_id: str,
    merchant_trans_id: str,
    merchant_prepare_id: str,
    amount: str,
    action: str,
    sign_time: str,
    sign_string: str,
    secret_key: str,
) -> bool:
    expected = _compute_sign(
        [
            click_trans_id,
            service_id,
            secret_key,
            merchant_trans_id,
            merchant_prepare_id,
            amount,
            action,
            sign_time,
        ]
    )
    return expected == sign_string


def _prepare_id_for(click_trans_id: str) -> int:
    # Deterministic prepare id Click echoes back in Complete (kept consistent so the
    # Complete signature, which includes it, recomputes correctly).
    return int(click_trans_id) if click_trans_id.isdigit() else abs(hash(click_trans_id))


def _amount_matches(amount: str) -> bool:
    price = billing.price_uzs_for_plan(_PLAN)
    try:
        return price is not None and abs(float(amount) - float(price)) < 0.01
    except ValueError:
        return False


@router.post("/prepare")
async def prepare(
    click_trans_id: Annotated[str, Form()],
    service_id: Annotated[str, Form()],
    merchant_trans_id: Annotated[str, Form()],
    amount: Annotated[str, Form()],
    action: Annotated[str, Form()],
    sign_time: Annotated[str, Form()],
    sign_string: Annotated[str, Form()],
    error: Annotated[str | None, Form()] = None,
    error_note: Annotated[str | None, Form()] = None,
) -> dict[str, Any]:
    base = {"click_trans_id": click_trans_id, "merchant_trans_id": merchant_trans_id}

    if not verify_prepare_sign(
        click_trans_id=click_trans_id,
        service_id=service_id,
        merchant_trans_id=merchant_trans_id,
        amount=amount,
        action=action,
        sign_time=sign_time,
        sign_string=sign_string,
        secret_key=settings.click_secret_key,
    ):
        return {**base, "error": ERR_SIGN_CHECK_FAILED, "error_note": "SIGN CHECK FAILED"}

    if not _amount_matches(amount):
        return {**base, "error": ERR_INCORRECT_AMOUNT, "error_note": "Incorrect amount"}

    user_id = merchant_trans_id
    if not await billing.user_exists(user_id):
        return {**base, "error": ERR_USER_NOT_FOUND, "error_note": "User not found"}

    prepare_id = _prepare_id_for(click_trans_id)
    await billing.record_transaction(
        user_id=user_id,
        provider="click",
        provider_tx_id=click_trans_id,
        state=1,  # created
        amount_uzs=int(float(amount)),
        raw={"stage": "prepare", "merchant_prepare_id": prepare_id},
    )
    return {
        **base,
        "merchant_prepare_id": prepare_id,
        "error": SUCCESS,
        "error_note": "Success",
    }


@router.post("/complete")
async def complete(
    click_trans_id: Annotated[str, Form()],
    service_id: Annotated[str, Form()],
    merchant_trans_id: Annotated[str, Form()],
    merchant_prepare_id: Annotated[str, Form()],
    amount: Annotated[str, Form()],
    action: Annotated[str, Form()],
    sign_time: Annotated[str, Form()],
    sign_string: Annotated[str, Form()],
    error: Annotated[str | None, Form()] = None,
    error_note: Annotated[str | None, Form()] = None,
) -> dict[str, Any]:
    base = {"click_trans_id": click_trans_id, "merchant_trans_id": merchant_trans_id}

    if not verify_complete_sign(
        click_trans_id=click_trans_id,
        service_id=service_id,
        merchant_trans_id=merchant_trans_id,
        merchant_prepare_id=merchant_prepare_id,
        amount=amount,
        action=action,
        sign_time=sign_time,
        sign_string=sign_string,
        secret_key=settings.click_secret_key,
    ):
        return {**base, "error": ERR_SIGN_CHECK_FAILED, "error_note": "SIGN CHECK FAILED"}

    user_id = merchant_trans_id

    # Click signals a user-side cancellation with a negative `error` field.
    if error is not None and error.lstrip("-").isdigit() and int(error) < 0:
        await billing.deactivate_subscription(user_id, "click")
        await billing.record_transaction(
            user_id=user_id,
            provider="click",
            provider_tx_id=click_trans_id,
            state=-2,
            amount_uzs=int(float(amount)),
            raw={"stage": "complete", "click_error": error},
        )
        return {
            **base,
            "merchant_confirm_id": _prepare_id_for(click_trans_id),
            "error": ERR_TRANS_CANCELLED,
            "error_note": "Transaction cancelled",
        }

    await billing.activate_subscription(user_id, provider="click", plan=_PLAN)
    await billing.record_transaction(
        user_id=user_id,
        provider="click",
        provider_tx_id=click_trans_id,
        state=2,  # performed
        amount_uzs=int(float(amount)),
        raw={"stage": "complete"},
    )
    return {
        **base,
        "merchant_confirm_id": _prepare_id_for(click_trans_id),
        "error": SUCCESS,
        "error_note": "Success",
    }
