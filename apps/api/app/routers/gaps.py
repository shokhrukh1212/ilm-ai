import json
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from .. import db
from ..auth import get_current_user_id
from ..services.gap_detection import run_gap_detection

router = APIRouter(prefix="/api/v1/gaps", tags=["gaps"])


class GapOut(BaseModel):
    id: int
    topic: str
    severity: int | None
    material_id: str | None
    evidence: dict[str, Any] | None
    status: str
    created_at: datetime


def _row_to_gap(row: Any) -> GapOut:
    evidence = row["evidence"]
    if isinstance(evidence, str):
        evidence = json.loads(evidence)
    return GapOut(
        id=int(row["id"]),
        topic=row["topic"],
        severity=row["severity"],
        material_id=row["material_id"],
        evidence=evidence,
        status=row["status"],
        created_at=row["created_at"],
    )


async def _list_open_gaps(user_id: str) -> list[GapOut]:
    connection = await db.connect()
    try:
        rows = await connection.fetch(
            """
            SELECT id, topic, severity, material_id::text AS material_id,
                   evidence, status, created_at
            FROM public.knowledge_gaps
            WHERE user_id = $1::uuid AND status = 'open'
            ORDER BY severity DESC NULLS LAST, updated_at DESC
            """,
            user_id,
        )
    finally:
        await connection.close()
    return [_row_to_gap(row) for row in rows]


@router.get("")
async def list_gaps(
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> list[GapOut]:
    return await _list_open_gaps(user_id)


@router.post("/detect")
async def detect(
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> list[GapOut]:
    await run_gap_detection(user_id)
    return await _list_open_gaps(user_id)
