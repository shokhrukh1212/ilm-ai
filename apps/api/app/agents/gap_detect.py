import json

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider

GAP_DETECT_MODEL = "claude-sonnet-4-6"
GAP_DETECT_PROMPT_VARIANT = "gapdetect-v1"
GAP_DETECT_RETRIES = 2

# Exact system prompt from blueprint §5 (Knowledge Gap Detection). It is static
# (describes the input/output contract), so it is used as the system prompt; the
# actual quiz-history list is passed as the run input.
GAP_DETECT_SYSTEM_PROMPT = """\
You analyze quiz history to surface knowledge gaps.

Input: list of {question, topic_tags, correct_answer, user_answer, is_correct, source_chunk_ids}.

Output JSON only:
{ "gaps": [
  { "topic": str,
    "severity": 1-5,
    "evidence_question_ids": [int],
    "suggested_review": str }
] }

Rules:
- Cluster wrong answers by topic, not by question.
- severity = round((wrong_count_in_topic / total_in_topic) * 5).
- One specific suggested_review per gap (e.g., "Re-read pages 14-18 then redo quiz set B").
- Max 5 gaps; merge similar ones.\
"""


class KnowledgeGapOut(BaseModel):
    topic: str
    severity: int = Field(ge=1, le=5)
    evidence_question_ids: list[int]
    suggested_review: str


class GapSet(BaseModel):
    gaps: list[KnowledgeGapOut]


_gap_detect_agent: Agent[None, GapSet] | None = None


def get_gap_detect_agent() -> Agent[None, GapSet]:
    global _gap_detect_agent
    if _gap_detect_agent is None:
        from ..settings import settings
        model = AnthropicModel(
            GAP_DETECT_MODEL,
            provider=AnthropicProvider(api_key=settings.anthropic_api_key),
        )
        _gap_detect_agent = Agent(
            model,
            output_type=GapSet,
            system_prompt=GAP_DETECT_SYSTEM_PROMPT,
            retries=GAP_DETECT_RETRIES,
        )
    return _gap_detect_agent


async def detect_gaps(history: list[dict[str, object]]) -> GapSet:
    result = await get_gap_detect_agent().run(json.dumps(history, ensure_ascii=False))
    return result.output
