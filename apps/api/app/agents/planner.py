from typing import Literal

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider

PLANNER_MODEL = "claude-sonnet-4-6"
PLANNER_PROMPT_VARIANT = "planner-v1"
PLANNER_RETRIES = 2

# Exact prompt from blueprint §5 (Learning Plan), with {minutes_per_day},
# {target_date}, {lang} placeholders preserved. The prompt is per-request, so it
# is formatted and delivered as the run input (same pattern as the quiz
# generator/explainer).
PLANNER_PROMPT_TEMPLATE = """\
You are a study planner. Given gaps, the learner's available daily time ({minutes_per_day} min), \
target date ({target_date}), and language {lang}, create a day-by-day plan.

Output JSON only:
{{ "plan": [
  {{ "date": "YYYY-MM-DD",
    "tasks": [
      {{ "type": "read"|"quiz"|"review"|"flashcards",
        "title": str,
        "estimated_minutes": int,
        "material_id": str|null,
        "gap_topic": str|null }}
    ] }}
] }}

Rules:
- Apply spaced repetition: re-review on days 1, 3, 7, 14 after first encounter.
- Highest-severity gaps front-loaded.
- No day exceeds minutes_per_day.
- Mix task types — never more than 2 of the same type per day.
- Final 2 days = full mock quiz + review.
- All task titles in {lang}."""


class PlanTask(BaseModel):
    type: Literal["read", "quiz", "review", "flashcards"]
    title: str
    estimated_minutes: int
    material_id: str | None
    gap_topic: str | None


class PlanDay(BaseModel):
    date: str
    tasks: list[PlanTask]


class LearningPlan(BaseModel):
    plan: list[PlanDay]


_planner_agent: Agent[None, LearningPlan] | None = None


def get_planner_agent() -> Agent[None, LearningPlan]:
    global _planner_agent
    if _planner_agent is None:
        from ..settings import settings
        model = AnthropicModel(
            PLANNER_MODEL,
            provider=AnthropicProvider(api_key=settings.anthropic_api_key),
        )
        _planner_agent = Agent(model, output_type=LearningPlan, retries=PLANNER_RETRIES)
    return _planner_agent


def build_planner_prompt(
    minutes_per_day: int,
    target_date: str,
    lang: str,
    gaps_json: str,
) -> str:
    base = PLANNER_PROMPT_TEMPLATE.format(
        minutes_per_day=minutes_per_day,
        target_date=target_date,
        lang=lang,
    )
    return f"{base}\n\n<gaps>\n{gaps_json}\n</gaps>"


async def generate_plan(
    minutes_per_day: int,
    target_date: str,
    lang: str,
    gaps_json: str,
) -> LearningPlan:
    prompt = build_planner_prompt(minutes_per_day, target_date, lang, gaps_json)
    result = await get_planner_agent().run(prompt)
    return result.output
