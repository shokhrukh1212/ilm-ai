import json
from datetime import date, datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from .. import db
from ..agents.planner import PLANNER_MODEL, generate_plan
from ..auth import get_current_user_id

router = APIRouter(prefix="/api/v1/plan", tags=["plan"])

DEFAULT_PLAN_DAYS = 7
DEFAULT_LANG = "uz-latn"


class GeneratePlanRequest(BaseModel):
    minutes_per_day: int = Field(..., ge=5, le=240)
    target_date: date | None = None


class ToggleTaskRequest(BaseModel):
    date: str
    task_index: int = Field(..., ge=0)
    done: bool


class StoredTask(BaseModel):
    type: str
    title: str
    estimated_minutes: int
    material_id: str | None = None
    gap_topic: str | None = None
    done: bool = False


class StoredDay(BaseModel):
    date: str
    tasks: list[StoredTask]


class LearningPlanOut(BaseModel):
    id: str
    start_date: date | None
    end_date: date | None
    plan: list[StoredDay]
    created_at: datetime


def _parse_plan_jsonb(raw: Any) -> list[dict[str, Any]]:
    if raw is None:
        return []
    if isinstance(raw, str):
        raw = json.loads(raw)
    if isinstance(raw, dict):
        return list(raw.get("plan", []))
    return list(raw)


def _row_to_plan(row: Any) -> LearningPlanOut:
    days = _parse_plan_jsonb(row["plan"])
    return LearningPlanOut(
        id=row["id"],
        start_date=row["start_date"],
        end_date=row["end_date"],
        plan=[StoredDay.model_validate(day) for day in days],
        created_at=row["created_at"],
    )


@router.post("/generate")
async def generate(
    req: GeneratePlanRequest,
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> LearningPlanOut:
    start = date.today()
    target = req.target_date or (start + timedelta(days=DEFAULT_PLAN_DAYS))

    connection = await db.connect()
    try:
        profile = await connection.fetchrow(
            "SELECT lang FROM public.users WHERE id = $1::uuid",
            user_id,
        )
        gap_rows = await connection.fetch(
            """
            SELECT topic, severity, material_id::text AS material_id, evidence
            FROM public.knowledge_gaps
            WHERE user_id = $1::uuid AND status = 'open'
            ORDER BY severity DESC NULLS LAST
            """,
            user_id,
        )
    finally:
        await connection.close()

    lang = (profile["lang"] if profile else None) or DEFAULT_LANG
    gaps_payload = [
        {
            "topic": row["topic"],
            "severity": row["severity"],
            "material_id": row["material_id"],
            "suggested_review": _suggested_review(row["evidence"]),
        }
        for row in gap_rows
    ]
    gaps_json = json.dumps(gaps_payload, ensure_ascii=False)

    learning_plan = await generate_plan(
        minutes_per_day=req.minutes_per_day,
        target_date=target.isoformat(),
        lang=lang,
        gaps_json=gaps_json,
    )

    # Persist with a `done` flag injected into every task.
    stored = {
        "plan": [
            {
                "date": day.date,
                "tasks": [
                    {
                        "type": task.type,
                        "title": task.title,
                        "estimated_minutes": task.estimated_minutes,
                        "material_id": task.material_id,
                        "gap_topic": task.gap_topic,
                        "done": False,
                    }
                    for task in day.tasks
                ],
            }
            for day in learning_plan.plan
        ]
    }

    connection = await db.connect()
    try:
        row = await connection.fetchrow(
            """
            INSERT INTO public.learning_plans
              (user_id, start_date, end_date, plan, generated_by)
            VALUES ($1::uuid, $2, $3, $4::jsonb, $5)
            RETURNING id::text, start_date, end_date, plan, created_at
            """,
            user_id,
            start,
            target,
            json.dumps(stored, ensure_ascii=False),
            PLANNER_MODEL,
        )
    finally:
        await connection.close()

    return _row_to_plan(row)


@router.get("")
async def get_plan(
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> LearningPlanOut | None:
    connection = await db.connect()
    try:
        row = await connection.fetchrow(
            """
            SELECT id::text, start_date, end_date, plan, created_at
            FROM public.learning_plans
            WHERE user_id = $1::uuid
            ORDER BY created_at DESC
            LIMIT 1
            """,
            user_id,
        )
    finally:
        await connection.close()
    if row is None:
        return None
    return _row_to_plan(row)


@router.post("/{plan_id}/task")
async def toggle_task(
    plan_id: str,
    req: ToggleTaskRequest,
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> LearningPlanOut:
    connection = await db.connect()
    try:
        async with connection.transaction():
            row = await connection.fetchrow(
                """
                SELECT id::text, start_date, end_date, plan, created_at
                FROM public.learning_plans
                WHERE id = $1::uuid AND user_id = $2::uuid
                FOR UPDATE
                """,
                plan_id,
                user_id,
            )
            if row is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Reja topilmadi"
                )

            days = _parse_plan_jsonb(row["plan"])
            target_day = next((d for d in days if d.get("date") == req.date), None)
            if target_day is None or req.task_index >= len(target_day.get("tasks", [])):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Vazifa topilmadi"
                )
            target_day["tasks"][req.task_index]["done"] = req.done

            await connection.execute(
                "UPDATE public.learning_plans SET plan = $2::jsonb WHERE id = $1::uuid",
                plan_id,
                json.dumps({"plan": days}, ensure_ascii=False),
            )
            updated = dict(row)
            updated["plan"] = {"plan": days}
    finally:
        await connection.close()

    return _row_to_plan(updated)


def _suggested_review(evidence: Any) -> str | None:
    if evidence is None:
        return None
    if isinstance(evidence, str):
        try:
            evidence = json.loads(evidence)
        except json.JSONDecodeError:
            return None
    if isinstance(evidence, dict):
        value = evidence.get("suggested_review")
        return str(value) if value is not None else None
    return None
