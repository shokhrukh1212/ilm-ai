from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..auth import get_current_user_id
from ..services import telegram_service as svc
from ..settings import settings

router = APIRouter(prefix="/api/v1/telegram", tags=["telegram"])


class LinkStartResponse(BaseModel):
    code: str
    bot_username: str


class LinkStatusResponse(BaseModel):
    linked: bool
    opt_in_daily: bool


class OptInRequest(BaseModel):
    opt_in: bool


@router.post("/link/start")
async def link_start(
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> LinkStartResponse:
    code = await svc.create_link_code(user_id)
    return LinkStartResponse(code=code, bot_username=settings.telegram_bot_username)


@router.get("/link/status")
async def link_status(
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> LinkStatusResponse:
    status = await svc.link_status(user_id)
    return LinkStatusResponse(**status)


@router.post("/link/opt-in")
async def link_opt_in(
    req: OptInRequest,
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> LinkStatusResponse:
    status = await svc.set_opt_in(user_id, req.opt_in)
    return LinkStatusResponse(**status)
