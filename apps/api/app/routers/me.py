from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, status

from ..auth import get_current_user_id
from ..settings import settings

router = APIRouter(prefix="/api/v1", tags=["me"])


@router.get("/me")
async def get_me(
    user_id: Annotated[str, Depends(get_current_user_id)],
    authorization: Annotated[str, Header()],
) -> dict[str, Any]:
    url = f"{settings.supabase_url}/rest/v1/users"
    headers = {
        "apikey": settings.supabase_anon_key,
        "Authorization": authorization,
        "Accept": "application/json",
    }
    params = {"id": f"eq.{user_id}", "select": "*"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)
    if response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Database error")
    rows: list[dict[str, Any]] = response.json()
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return rows[0]
