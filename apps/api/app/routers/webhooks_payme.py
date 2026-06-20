"""Native Payme (Paycom) Merchant API webhook — JSON-RPC 2.0 at POST /webhooks/payme.

Authenticated with HTTP Basic ``Paycom:{PAYME_KEY}``. Implements the six merchant
methods. ``account.user_id`` carries the payer; amounts arrive in tiyin (1 UZS = 100
tiyin) and are validated against the Talaba price. A performed transaction activates the
Talaba tier; a cancelled one deactivates it. Transaction state lives in
``payment_transactions`` (state 1=created, 2=performed, -1=cancelled-pre-perform,
-2=cancelled-post-perform) with Payme millisecond timestamps stored in ``raw``.
"""

import base64
import logging
import time
from typing import Annotated, Any

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse

from ..services import billing
from ..settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Payme JSON-RPC error codes.
ERR_INSUFFICIENT_PRIVILEGE = -32504
ERR_METHOD_NOT_FOUND = -32601
ERR_INVALID_AMOUNT = -31001
ERR_TRANSACTION_NOT_FOUND = -31003
ERR_CANNOT_PERFORM = -31008
ERR_CANNOT_CANCEL = -31007
ERR_ACCOUNT_NOT_FOUND = -31050  # account-range error (user_id missing/invalid)

# Transaction states (ours, aligned to Payme conventions).
STATE_CREATED = 1
STATE_PERFORMED = 2
STATE_CANCELLED_PRE = -1
STATE_CANCELLED_POST = -2

_PLAN = "talaba"


def _now_ms() -> int:
    return int(time.time() * 1000)


def _error(req_id: Any, code: int, message: str, data: Any = None) -> JSONResponse:
    err: dict[str, Any] = {
        "code": code,
        "message": {"ru": message, "uz": message, "en": message},
    }
    if data is not None:
        err["data"] = data
    return JSONResponse({"error": err, "id": req_id})


def _result(req_id: Any, result: dict[str, Any]) -> JSONResponse:
    return JSONResponse({"result": result, "id": req_id})


def check_basic_auth(authorization: str | None, payme_key: str) -> bool:
    """Payme authenticates with HTTP Basic ``Paycom:{merchant_key}``."""
    if not authorization or not authorization.startswith("Basic "):
        return False
    try:
        decoded = base64.b64decode(authorization[6:]).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return False
    _, _, password = decoded.partition(":")
    return bool(payme_key) and password == payme_key


def _expected_amount_tiyin() -> int:
    price = billing.price_uzs_for_plan(_PLAN) or 0
    return price * 100


async def _resolve_account(params: dict[str, Any]) -> str | None:
    """Extract + validate the user id from a Payme account block."""
    account = params.get("account") or {}
    user_id = account.get("user_id")
    if not user_id:
        return None
    return user_id if await billing.user_exists(str(user_id)) else None


# --- Method handlers ------------------------------------------------------------------


async def _check_perform_transaction(req_id: Any, params: dict[str, Any]) -> JSONResponse:
    user_id = await _resolve_account(params)
    if user_id is None:
        return _error(
            req_id, ERR_ACCOUNT_NOT_FOUND, "Account not found", data="user_id"
        )
    if int(params.get("amount", 0)) != _expected_amount_tiyin():
        return _error(req_id, ERR_INVALID_AMOUNT, "Invalid amount")
    return _result(req_id, {"allow": True})


async def _create_transaction(req_id: Any, params: dict[str, Any]) -> JSONResponse:
    tx_id = str(params.get("id"))
    user_id = await _resolve_account(params)
    if user_id is None:
        return _error(
            req_id, ERR_ACCOUNT_NOT_FOUND, "Account not found", data="user_id"
        )
    if int(params.get("amount", 0)) != _expected_amount_tiyin():
        return _error(req_id, ERR_INVALID_AMOUNT, "Invalid amount")

    existing = await billing.get_transaction("payme", tx_id)
    if existing is not None:
        if existing["state"] != STATE_CREATED:
            return _error(req_id, ERR_CANNOT_PERFORM, "Transaction in invalid state")
        create_time = existing["raw"].get("create_time", _now_ms())
    else:
        create_time = _now_ms()
        await billing.record_transaction(
            user_id=user_id,
            provider="payme",
            provider_tx_id=tx_id,
            state=STATE_CREATED,
            amount_uzs=int(params.get("amount", 0)) // 100,
            raw={"create_time": create_time, "account": params.get("account")},
        )
    return _result(
        req_id,
        {"create_time": create_time, "transaction": tx_id, "state": STATE_CREATED},
    )


async def _perform_transaction(req_id: Any, params: dict[str, Any]) -> JSONResponse:
    tx_id = str(params.get("id"))
    tx = await billing.get_transaction("payme", tx_id)
    if tx is None:
        return _error(req_id, ERR_TRANSACTION_NOT_FOUND, "Transaction not found")

    if tx["state"] == STATE_PERFORMED:
        return _result(
            req_id,
            {
                "transaction": tx_id,
                "perform_time": tx["raw"].get("perform_time", _now_ms()),
                "state": STATE_PERFORMED,
            },
        )
    if tx["state"] != STATE_CREATED:
        return _error(req_id, ERR_CANNOT_PERFORM, "Transaction in invalid state")

    perform_time = _now_ms()
    raw = {**tx["raw"], "perform_time": perform_time}
    await billing.activate_subscription(tx["user_id"], provider="payme", plan=_PLAN)
    await billing.record_transaction(
        user_id=tx["user_id"],
        provider="payme",
        provider_tx_id=tx_id,
        state=STATE_PERFORMED,
        amount_uzs=tx["amount_uzs"],
        raw=raw,
    )
    return _result(
        req_id,
        {"transaction": tx_id, "perform_time": perform_time, "state": STATE_PERFORMED},
    )


async def _cancel_transaction(req_id: Any, params: dict[str, Any]) -> JSONResponse:
    tx_id = str(params.get("id"))
    tx = await billing.get_transaction("payme", tx_id)
    if tx is None:
        return _error(req_id, ERR_TRANSACTION_NOT_FOUND, "Transaction not found")

    already = tx["state"] in (STATE_CANCELLED_PRE, STATE_CANCELLED_POST)
    new_state = STATE_CANCELLED_POST if tx["state"] == STATE_PERFORMED else STATE_CANCELLED_PRE
    cancel_time = tx["raw"].get("cancel_time", _now_ms()) if already else _now_ms()

    if not already:
        raw = {**tx["raw"], "cancel_time": cancel_time, "reason": params.get("reason")}
        if tx["state"] == STATE_PERFORMED:
            await billing.deactivate_subscription(tx["user_id"], "payme")
        await billing.record_transaction(
            user_id=tx["user_id"],
            provider="payme",
            provider_tx_id=tx_id,
            state=new_state,
            amount_uzs=tx["amount_uzs"],
            raw=raw,
        )
    else:
        new_state = tx["state"]

    return _result(
        req_id,
        {"transaction": tx_id, "cancel_time": cancel_time, "state": new_state},
    )


async def _check_transaction(req_id: Any, params: dict[str, Any]) -> JSONResponse:
    tx_id = str(params.get("id"))
    tx = await billing.get_transaction("payme", tx_id)
    if tx is None:
        return _error(req_id, ERR_TRANSACTION_NOT_FOUND, "Transaction not found")
    raw = tx["raw"]
    return _result(
        req_id,
        {
            "create_time": raw.get("create_time", 0),
            "perform_time": raw.get("perform_time", 0),
            "cancel_time": raw.get("cancel_time", 0),
            "transaction": tx_id,
            "state": tx["state"],
            "reason": raw.get("reason"),
        },
    )


async def _get_statement(req_id: Any, params: dict[str, Any]) -> JSONResponse:
    # Minimal statement: Payme reconciliation. Returns an empty window by default;
    # a full ledger export can be added in observability (Phase 8).
    return _result(req_id, {"transactions": []})


_METHODS = {
    "CheckPerformTransaction": _check_perform_transaction,
    "CreateTransaction": _create_transaction,
    "PerformTransaction": _perform_transaction,
    "CancelTransaction": _cancel_transaction,
    "CheckTransaction": _check_transaction,
    "GetStatement": _get_statement,
}


@router.post("/payme")
async def payme_webhook(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> JSONResponse:
    body = await request.json()
    req_id = body.get("id")

    if not check_basic_auth(authorization, settings.payme_key):
        return _error(req_id, ERR_INSUFFICIENT_PRIVILEGE, "Insufficient privilege")

    method = body.get("method")
    params = body.get("params") or {}
    handler = _METHODS.get(method)
    if handler is None:
        return _error(req_id, ERR_METHOD_NOT_FOUND, "Method not found")

    return await handler(req_id, params)
