import asyncio
import json
import logging
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field

from .. import db
from ..agents.quiz_explainer import explain
from ..agents.quiz_gen import generate_quiz
from ..auth import get_current_user_id
from ..services.citations import build_citations_for_chunk_ids
from ..services.gap_detection import run_gap_detection
from ..services.quiz_sources import build_sources_block, fetch_quiz_sources

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/quiz", tags=["quiz"])

GENERATE_TIMEOUT_S = 15.0
DEFAULT_LANG = "uz-latn"


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class GenerateRequest(BaseModel):
    material_id: UUID
    num_questions: int = Field(default=10, ge=5, le=20)
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    lang: str | None = None


class QuestionPublic(BaseModel):
    id: int
    type: str
    prompt: str
    options: list[str] | None


class GenerateResponse(BaseModel):
    session_id: str
    questions: list[QuestionPublic]


class TakeView(BaseModel):
    session_id: str
    material_id: str
    lang: str | None
    difficulty: str | None
    num_questions: int | None
    completed_at: Any | None
    questions: list[QuestionPublic]
    answered_question_ids: list[int]


class AnswerRequest(BaseModel):
    question_id: int
    user_answer: str = Field(..., max_length=4000)
    time_spent_s: int | None = None


class AnswerResponse(BaseModel):
    is_correct: bool
    feedback: str
    correct_answer: str
    rationale: str
    citations: list[dict[str, Any]]


class FinishResponse(BaseModel):
    score: float
    correct_count: int
    total: int


class ResultQuestion(BaseModel):
    id: int
    type: str
    prompt: str
    options: list[str] | None
    correct_answer: str
    rationale: str
    citations: list[dict[str, Any]]
    user_answer: str | None
    is_correct: bool | None
    ai_feedback: str | None


class ResultsResponse(BaseModel):
    session_id: str
    material_id: str
    lang: str | None
    difficulty: str | None
    score: float | None
    correct_count: int
    total: int
    questions: list[ResultQuestion]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _owned_session(connection: Any, session_id: str, user_id: str) -> Any:
    row = await connection.fetchrow(
        """
        SELECT id::text, material_id::text, lang, difficulty, num_questions, score, completed_at
        FROM public.quiz_sessions
        WHERE id = $1::uuid AND user_id = $2::uuid
        """,
        session_id,
        user_id,
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz topilmadi")
    return row


async def _source_text_for_question(connection: Any, chunk_ids: list[int]) -> str:
    if not chunk_ids:
        return ""
    rows = await connection.fetch(
        """
        SELECT id, content FROM public.chunks WHERE id = ANY($1::bigint[])
        """,
        chunk_ids,
    )
    by_id = {int(r["id"]): str(r["content"]) for r in rows}
    return "\n".join(
        f"[chunk {cid}] {by_id[cid]}" for cid in chunk_ids if cid in by_id
    )


async def _citation_dicts(chunk_ids: list[int]) -> list[dict[str, Any]]:
    citations = await build_citations_for_chunk_ids(chunk_ids)
    return [
        {
            "index": c.index,
            "chunk_id": c.chunk_id,
            "material_id": c.material_id,
            "material_title": c.material_title,
            "page": c.page,
            "snippet": c.snippet,
        }
        for c in citations
    ]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/generate")
async def generate(
    req: GenerateRequest,
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> GenerateResponse:
    material_id = str(req.material_id)

    connection = await db.connect()
    try:
        material = await connection.fetchrow(
            """
            SELECT status, lang_detected FROM public.materials
            WHERE id = $1::uuid AND user_id = $2::uuid
            """,
            material_id,
            user_id,
        )
    finally:
        await connection.close()

    if material is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material topilmadi")
    if material["status"] != "ready":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Material hali tayyor emas",
        )

    chunks = await fetch_quiz_sources(material_id, user_id)
    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Materialda savol yaratish uchun matn topilmadi",
        )

    lang = req.lang or material["lang_detected"] or DEFAULT_LANG
    sources_block = build_sources_block(chunks)

    try:
        quiz_set = await asyncio.wait_for(
            generate_quiz(req.num_questions, lang, req.difficulty, sources_block),
            timeout=GENERATE_TIMEOUT_S,
        )
    except asyncio.TimeoutError:
        logger.warning("quiz generation timed out material=%s", material_id)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Savollar yaratish juda uzoq davom etdi. Qayta urinib ko'ring.",
        )
    except Exception:
        logger.exception("quiz generation failed material=%s", material_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Savollar yaratishda xato yuz berdi",
        )

    valid_chunk_ids = {c.chunk_id for c in chunks}

    connection = await db.connect()
    try:
        async with connection.transaction():
            session_id: str = await connection.fetchval(
                """
                INSERT INTO public.quiz_sessions
                  (user_id, material_id, lang, difficulty, num_questions)
                VALUES ($1::uuid, $2::uuid, $3, $4, $5)
                RETURNING id::text
                """,
                user_id,
                material_id,
                lang,
                req.difficulty,
                len(quiz_set.questions),
            )
            public_questions: list[QuestionPublic] = []
            for ord_idx, q in enumerate(quiz_set.questions):
                # Keep only chunk ids that came from this material's sources.
                source_ids = [cid for cid in q.source_chunk_ids if cid in valid_chunk_ids]
                qid: int = await connection.fetchval(
                    """
                    INSERT INTO public.quiz_questions
                      (session_id, type, prompt, options, correct_answer,
                       rationale, source_chunk_ids, ord)
                    VALUES ($1::uuid, $2, $3, $4::jsonb, $5, $6, $7::bigint[], $8)
                    RETURNING id
                    """,
                    session_id,
                    q.type,
                    q.prompt,
                    json.dumps(q.options) if q.options is not None else None,
                    q.correct_answer,
                    q.rationale,
                    source_ids,
                    ord_idx,
                )
                public_questions.append(
                    QuestionPublic(id=qid, type=q.type, prompt=q.prompt, options=q.options)
                )
    finally:
        await connection.close()

    return GenerateResponse(session_id=session_id, questions=public_questions)


@router.get("/{session_id}")
async def get_take(
    session_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> TakeView:
    connection = await db.connect()
    try:
        session = await _owned_session(connection, session_id, user_id)
        rows = await connection.fetch(
            """
            SELECT id, type, prompt, options
            FROM public.quiz_questions
            WHERE session_id = $1::uuid
            ORDER BY ord ASC
            """,
            session_id,
        )
        answered = await connection.fetch(
            """
            SELECT a.question_id
            FROM public.quiz_answers a
            JOIN public.quiz_questions q ON q.id = a.question_id
            WHERE q.session_id = $1::uuid
            """,
            session_id,
        )
    finally:
        await connection.close()

    return TakeView(
        session_id=session["id"],
        material_id=session["material_id"],
        lang=session["lang"],
        difficulty=session["difficulty"],
        num_questions=session["num_questions"],
        completed_at=session["completed_at"],
        questions=[_question_public(row) for row in rows],
        answered_question_ids=[int(r["question_id"]) for r in answered],
    )


@router.post("/{session_id}/answer")
async def answer(
    session_id: str,
    req: AnswerRequest,
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> AnswerResponse:
    connection = await db.connect()
    try:
        session = await _owned_session(connection, session_id, user_id)
        question = await connection.fetchrow(
            """
            SELECT id, type, prompt, options, correct_answer, rationale, source_chunk_ids
            FROM public.quiz_questions
            WHERE id = $1::bigint AND session_id = $2::uuid
            """,
            req.question_id,
            session_id,
        )
        if question is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Savol topilmadi")
        source_chunk_ids = list(question["source_chunk_ids"] or [])
        source_text = await _source_text_for_question(connection, source_chunk_ids)
    finally:
        await connection.close()

    lang = session["lang"] or DEFAULT_LANG
    correct_answer = question["correct_answer"] or ""
    deterministic_correct = (
        req.user_answer.strip() == correct_answer.strip()
        if question["type"] == "mcq"
        else None
    )

    try:
        explanation = await explain(
            lang=lang,
            prompt=question["prompt"],
            correct_answer=correct_answer,
            user_answer=req.user_answer,
            source_text=source_text,
        )
        feedback = explanation.feedback
        is_correct = (
            deterministic_correct
            if deterministic_correct is not None
            else explanation.is_correct
        )
    except Exception:
        logger.exception("quiz explain failed question=%s", req.question_id)
        # Fall back to deterministic grading (MCQ) or no judgement (open).
        is_correct = bool(deterministic_correct)
        feedback = ""

    connection = await db.connect()
    try:
        await connection.execute(
            """
            DELETE FROM public.quiz_answers WHERE question_id = $1::bigint
            """,
            req.question_id,
        )
        await connection.execute(
            """
            INSERT INTO public.quiz_answers
              (question_id, user_answer, is_correct, ai_feedback, time_spent_s)
            VALUES ($1::bigint, $2, $3, $4, $5)
            """,
            req.question_id,
            req.user_answer,
            is_correct,
            feedback,
            req.time_spent_s,
        )
    finally:
        await connection.close()

    citations = await _citation_dicts(source_chunk_ids)

    return AnswerResponse(
        is_correct=bool(is_correct),
        feedback=feedback,
        correct_answer=correct_answer,
        rationale=question["rationale"] or "",
        citations=citations,
    )


@router.post("/{session_id}/finish")
async def finish(
    session_id: str,
    background_tasks: BackgroundTasks,
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> FinishResponse:
    connection = await db.connect()
    try:
        await _owned_session(connection, session_id, user_id)
        total = await connection.fetchval(
            "SELECT count(*) FROM public.quiz_questions WHERE session_id = $1::uuid",
            session_id,
        )
        correct = await connection.fetchval(
            """
            SELECT count(*)
            FROM public.quiz_answers a
            JOIN public.quiz_questions q ON q.id = a.question_id
            WHERE q.session_id = $1::uuid AND a.is_correct = true
            """,
            session_id,
        )
        total_int = int(total)
        correct_int = int(correct)
        score = (correct_int / total_int) if total_int else 0.0
        await connection.execute(
            """
            UPDATE public.quiz_sessions
            SET score = $2, completed_at = now()
            WHERE id = $1::uuid
            """,
            session_id,
            score,
        )
    finally:
        await connection.close()

    # Re-analyze the learner's recent quiz history to refresh knowledge gaps.
    background_tasks.add_task(run_gap_detection, user_id)

    return FinishResponse(score=score, correct_count=correct_int, total=total_int)


@router.get("/{session_id}/results")
async def results(
    session_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> ResultsResponse:
    connection = await db.connect()
    try:
        session = await _owned_session(connection, session_id, user_id)
        rows = await connection.fetch(
            """
            SELECT
              q.id, q.type, q.prompt, q.options, q.correct_answer, q.rationale,
              q.source_chunk_ids,
              a.user_answer, a.is_correct, a.ai_feedback
            FROM public.quiz_questions q
            LEFT JOIN public.quiz_answers a ON a.question_id = q.id
            WHERE q.session_id = $1::uuid
            ORDER BY q.ord ASC
            """,
            session_id,
        )
    finally:
        await connection.close()

    result_questions: list[ResultQuestion] = []
    correct_count = 0
    for row in rows:
        if row["is_correct"]:
            correct_count += 1
        chunk_ids = list(row["source_chunk_ids"] or [])
        citations = await _citation_dicts(chunk_ids)
        result_questions.append(
            ResultQuestion(
                id=int(row["id"]),
                type=row["type"],
                prompt=row["prompt"],
                options=_parse_options(row["options"]),
                correct_answer=row["correct_answer"] or "",
                rationale=row["rationale"] or "",
                citations=citations,
                user_answer=row["user_answer"],
                is_correct=row["is_correct"],
                ai_feedback=row["ai_feedback"],
            )
        )

    return ResultsResponse(
        session_id=session["id"],
        material_id=session["material_id"],
        lang=session["lang"],
        difficulty=session["difficulty"],
        score=float(session["score"]) if session["score"] is not None else None,
        correct_count=correct_count,
        total=len(result_questions),
        questions=result_questions,
    )


def _parse_options(raw: Any) -> list[str] | None:
    if raw is None:
        return None
    if isinstance(raw, str):
        parsed = json.loads(raw)
        return list(parsed) if parsed is not None else None
    return list(raw)


def _question_public(row: Any) -> QuestionPublic:
    return QuestionPublic(
        id=int(row["id"]),
        type=row["type"],
        prompt=row["prompt"],
        options=_parse_options(row["options"]),
    )
