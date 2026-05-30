from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider

from .tutor import sanitize_user_message

EXPLAINER_MODEL = "claude-sonnet-4-6"
EXPLAINER_PROMPT_VARIANT = "quizexplain-v1"

# Exact prompt from blueprint §5 (Quiz Explainer), with {lang}, {prompt},
# {correct}, and {user_answer} placeholders preserved. The explainer prompt is
# fully per-answer, so it is formatted per request and delivered as the run
# input (the same pattern as the quiz generator), rather than baked into a
# static system prompt.
EXPLAINER_PROMPT_TEMPLATE = """\
You are explaining a quiz answer to a learner in {lang}. Question: {prompt}. Correct answer: {correct}. \
Learner's answer: {user_answer}.

If correct: 1-sentence affirmation + 1-sentence deeper insight.
If incorrect: do NOT shame. State the correct answer clearly. Explain why in 2-3 sentences using a concrete \
analogy. Reference the source chunk number.
Always end with one tiny next-step suggestion ("Try the related question about X next").
Tone: warm, ustoz-style. "Siz" in Uzbek.\
"""


class Explanation(BaseModel):
    is_correct: bool
    feedback: str


_quiz_explainer_agent: Agent[None, Explanation] | None = None


def get_quiz_explainer_agent() -> Agent[None, Explanation]:
    global _quiz_explainer_agent
    if _quiz_explainer_agent is None:
        from ..settings import settings
        model = AnthropicModel(
            EXPLAINER_MODEL,
            provider=AnthropicProvider(api_key=settings.anthropic_api_key),
        )
        _quiz_explainer_agent = Agent(model, output_type=Explanation)
    return _quiz_explainer_agent


def build_explainer_turn(
    lang: str,
    prompt: str,
    correct_answer: str,
    user_answer: str,
    source_text: str,
) -> str:
    """Format the exact blueprint explainer prompt plus grading context.

    The source chunk text is appended so the model can reference the source
    chunk number (per the blueprint prompt). The learner's answer is sanitized
    against prompt injection. The explainer also returns is_correct, which lets
    it grade open-ended answers.
    """
    safe_answer = sanitize_user_message(user_answer)
    base = EXPLAINER_PROMPT_TEMPLATE.format(
        lang=lang,
        prompt=prompt,
        correct=correct_answer,
        user_answer=safe_answer,
    )
    return (
        f"{base}\n\n"
        "Also decide whether the learner's answer is correct and set is_correct.\n"
        "<source>\n"
        f"{source_text}\n"
        "</source>"
    )


async def explain(
    lang: str,
    prompt: str,
    correct_answer: str,
    user_answer: str,
    source_text: str,
) -> Explanation:
    turn = build_explainer_turn(lang, prompt, correct_answer, user_answer, source_text)
    result = await get_quiz_explainer_agent().run(turn)
    return result.output
