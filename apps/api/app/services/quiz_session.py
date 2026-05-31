"""Shared quiz-session creation used by the web router and the Telegram bot.

Generates a grounded quiz from a material's chunks and persists the
``quiz_sessions`` + ``quiz_questions`` rows in one transaction. Callers handle
their own ownership/readiness checks and error presentation.
"""

import asyncio
import json

from pydantic import BaseModel

from .. import db
from ..agents.quiz_gen import QuizProvider, generate_quiz
from .quiz_sources import build_sources_block, fetch_quiz_sources


class QuizSourcesEmpty(Exception):
    """Raised when a material has no chunks to build questions from."""


class PersistedQuestion(BaseModel):
    id: int
    type: str
    prompt: str
    options: list[str] | None
    correct_answer: str
    rationale: str


async def create_quiz_session(
    user_id: str,
    material_id: str,
    num_questions: int,
    difficulty: str,
    lang: str,
    provider: QuizProvider = "openai",
    timeout_s: float | None = None,
) -> tuple[str, list[PersistedQuestion]]:
    chunks = await fetch_quiz_sources(material_id, user_id)
    if not chunks:
        raise QuizSourcesEmpty(material_id)

    sources_block = build_sources_block(chunks)
    gen = generate_quiz(num_questions, lang, difficulty, sources_block, provider=provider)
    quiz_set = await (asyncio.wait_for(gen, timeout=timeout_s) if timeout_s else gen)

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
                difficulty,
                len(quiz_set.questions),
            )
            persisted: list[PersistedQuestion] = []
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
                persisted.append(
                    PersistedQuestion(
                        id=int(qid),
                        type=q.type,
                        prompt=q.prompt,
                        options=q.options,
                        correct_answer=q.correct_answer,
                        rationale=q.rationale,
                    )
                )
    finally:
        await connection.close()

    return session_id, persisted
