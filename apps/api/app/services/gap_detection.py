import json
import logging
from collections import Counter
from typing import Any

from .. import db
from ..agents.gap_detect import GAP_DETECT_MODEL, KnowledgeGapOut, detect_gaps

logger = logging.getLogger(__name__)

HISTORY_WINDOW_DAYS = 90


async def run_gap_detection(user_id: str) -> None:
    """Background flow: analyze recent quiz history and upsert knowledge gaps.

    Runs after a quiz is finished. Failures (missing key, agent error) are
    logged and swallowed so the background task never crashes the request.
    """
    try:
        history, material_by_question = await _load_history(user_id)
        if not history:
            return
        gap_set = await detect_gaps(history)
        await _upsert_gaps(user_id, gap_set.gaps, material_by_question)
    except Exception:
        logger.exception("gap detection failed user=%s", user_id)


async def _load_history(
    user_id: str,
) -> tuple[list[dict[str, Any]], dict[int, str]]:
    connection = await db.connect()
    try:
        rows = await connection.fetch(
            """
            SELECT q.id, q.prompt, q.correct_answer, q.source_chunk_ids,
                   a.user_answer, a.is_correct,
                   s.material_id::text AS material_id
            FROM public.quiz_answers a
            JOIN public.quiz_questions q ON q.id = a.question_id
            JOIN public.quiz_sessions s ON s.id = q.session_id
            WHERE s.user_id = $1::uuid
              AND a.created_at >= now() - ($2 || ' days')::interval
            ORDER BY a.created_at ASC
            """,
            user_id,
            str(HISTORY_WINDOW_DAYS),
        )
    finally:
        await connection.close()

    history: list[dict[str, Any]] = []
    material_by_question: dict[int, str] = {}
    for row in rows:
        qid = int(row["id"])
        material_by_question[qid] = str(row["material_id"])
        history.append(
            {
                "question_id": qid,
                "question": row["prompt"],
                "correct_answer": row["correct_answer"],
                "user_answer": row["user_answer"],
                "is_correct": row["is_correct"],
                "source_chunk_ids": list(row["source_chunk_ids"] or []),
            }
        )
    return history, material_by_question


def _dominant_material(
    evidence_question_ids: list[int],
    material_by_question: dict[int, str],
) -> str | None:
    materials = [
        material_by_question[qid]
        for qid in evidence_question_ids
        if qid in material_by_question
    ]
    if not materials:
        return None
    return Counter(materials).most_common(1)[0][0]


async def _upsert_gaps(
    user_id: str,
    gaps: list[KnowledgeGapOut],
    material_by_question: dict[int, str],
) -> None:
    connection = await db.connect()
    try:
        async with connection.transaction():
            existing = await connection.fetch(
                """
                SELECT id, topic FROM public.knowledge_gaps
                WHERE user_id = $1::uuid AND status = 'open'
                """,
                user_id,
            )
            existing_by_topic = {
                _normalize(row["topic"]): int(row["id"]) for row in existing
            }

            detected_topics: set[str] = set()
            for gap in gaps:
                norm = _normalize(gap.topic)
                detected_topics.add(norm)
                material_id = _dominant_material(
                    gap.evidence_question_ids, material_by_question
                )
                evidence = json.dumps(
                    {
                        "question_ids": gap.evidence_question_ids,
                        "suggested_review": gap.suggested_review,
                    },
                    ensure_ascii=False,
                )
                gap_id = existing_by_topic.get(norm)
                if gap_id is not None:
                    await connection.execute(
                        """
                        UPDATE public.knowledge_gaps
                        SET severity = $2, evidence = $3::jsonb, material_id = $4::uuid,
                            status = 'open', updated_at = now()
                        WHERE id = $1::bigint
                        """,
                        gap_id,
                        gap.severity,
                        evidence,
                        material_id,
                    )
                else:
                    await connection.execute(
                        """
                        INSERT INTO public.knowledge_gaps
                          (user_id, material_id, topic, severity, evidence, status)
                        VALUES ($1::uuid, $2::uuid, $3, $4, $5::jsonb, 'open')
                        """,
                        user_id,
                        material_id,
                        gap.topic,
                        gap.severity,
                        evidence,
                    )

            # Close previously-open gaps that no longer appear.
            stale_ids = [
                gap_id
                for norm, gap_id in existing_by_topic.items()
                if norm not in detected_topics
            ]
            if stale_ids:
                await connection.execute(
                    """
                    UPDATE public.knowledge_gaps
                    SET status = 'closed', updated_at = now()
                    WHERE id = ANY($1::bigint[])
                    """,
                    stale_ids,
                )
    finally:
        await connection.close()


def _normalize(topic: str) -> str:
    return topic.strip().lower()


# Re-exported for callers/tests that want the model name used to tag plans/gaps.
__all__ = ["run_gap_detection", "GAP_DETECT_MODEL"]
