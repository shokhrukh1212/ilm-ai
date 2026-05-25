import json
import logging
import time
from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from .. import db
from ..agents.tutor import (
    PROMPT_VARIANT,
    TUTOR_MODEL,
    TutorUsage,
    build_user_turn,
    citation_to_dict,
    get_tutor_agent,
    postfilter_citations,
)
from ..auth import get_current_user_id
from ..services.citations import build_citations
from ..services.retrieve import retrieve

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


class ChatRequest(BaseModel):
    material_ids: list[UUID] = Field(..., min_length=1)
    message: str = Field(..., min_length=1, max_length=4000)
    lang: str | None = None
    session_id: UUID | None = None


async def _ensure_session(
    user_id: str,
    material_ids: list[str],
    message: str,
    session_id: str | None,
) -> str:
    title = message[:60]
    connection = await db.connect()
    try:
        if session_id:
            row = await connection.fetchrow(
                "SELECT id FROM public.chat_sessions WHERE id = $1::uuid AND user_id = $2::uuid",
                session_id,
                user_id,
            )
            if row:
                return session_id
        sid: str = await connection.fetchval(
            """
            INSERT INTO public.chat_sessions (user_id, material_ids, title)
            VALUES ($1::uuid, $2::uuid[], $3)
            RETURNING id::text
            """,
            user_id,
            material_ids,
            title,
        )
        return sid
    finally:
        await connection.close()


async def _save_user_message(session_id: str, content: str) -> None:
    connection = await db.connect()
    try:
        await connection.execute(
            """
            INSERT INTO public.chat_messages (session_id, role, content)
            VALUES ($1::uuid, 'user', $2)
            """,
            session_id,
            content,
        )
    finally:
        await connection.close()


async def _save_assistant_message(
    session_id: str,
    content: str,
    citations_json: object,
    usage: TutorUsage,
    latency_ms: int,
) -> None:
    connection = await db.connect()
    try:
        await connection.execute(
            """
            INSERT INTO public.chat_messages
              (session_id, role, content, citations, tokens_in, tokens_out,
               model, latency_ms, prompt_variant)
            VALUES ($1::uuid, 'assistant', $2, $3::jsonb, $4, $5, $6, $7, $8)
            """,
            session_id,
            content,
            json.dumps(citations_json),
            usage.tokens_in,
            usage.tokens_out,
            TUTOR_MODEL,
            latency_ms,
            PROMPT_VARIANT,
        )
    finally:
        await connection.close()


@router.post("")
async def chat(
    req: ChatRequest,
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> EventSourceResponse:
    material_ids = [str(mid) for mid in req.material_ids]

    connection = await db.connect()
    try:
        count = await connection.fetchval(
            """
            SELECT count(*) FROM public.materials
            WHERE id = ANY($1::uuid[]) AND user_id = $2::uuid
            """,
            material_ids,
            user_id,
        )
    finally:
        await connection.close()

    if int(count) != len(material_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more materials not found",
        )

    session_id = await _ensure_session(
        user_id, material_ids, req.message, str(req.session_id) if req.session_id else None
    )
    await _save_user_message(session_id, req.message)

    return EventSourceResponse(_event_generator(req, user_id, material_ids, session_id))


async def _event_generator(
    req: ChatRequest,
    user_id: str,
    material_ids: list[str],
    session_id: str,
) -> AsyncGenerator[dict[str, str], None]:
    start_ms = int(time.monotonic() * 1000)
    full_text = ""
    usage = TutorUsage(tokens_in=0, tokens_out=0)

    try:
        chunks = await retrieve(req.message, material_ids, user_id)
        citations = await build_citations(chunks)
        user_turn = build_user_turn(citations, req.message)

        async with get_tutor_agent().run_stream(user_turn) as stream_ctx:
            async for delta in stream_ctx.stream_text(delta=True):
                full_text += delta
                yield {"event": "token", "data": delta}

            raw_usage = stream_ctx.usage()
            usage.tokens_in = raw_usage.request_tokens or 0
            usage.tokens_out = raw_usage.response_tokens or 0

        final_text = postfilter_citations(full_text, len(citations))
        citations_payload = [citation_to_dict(c) for c in citations]

        yield {
            "event": "citations",
            "data": json.dumps({"citations": citations_payload, "session_id": session_id}),
        }
        yield {"event": "done", "data": json.dumps({"session_id": session_id})}

        latency_ms = int(time.monotonic() * 1000) - start_ms
        await _save_assistant_message(
            session_id, final_text, citations_payload, usage, latency_ms
        )

    except Exception:
        logger.exception("chat stream error session=%s", session_id)
        yield {"event": "error", "data": json.dumps({"detail": "So'rovni bajarishda xato yuz berdi"})}
