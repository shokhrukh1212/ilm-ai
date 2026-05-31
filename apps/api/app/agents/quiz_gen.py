from typing import Literal

from pydantic import BaseModel, model_validator
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.openai import OpenAIProvider

QuizProvider = Literal["openai", "anthropic"]

QUIZ_GEN_MODEL = "gpt-4o"
# Anthropic fallback used where no OpenAI key is configured (e.g. the Telegram bot).
QUIZ_GEN_MODEL_ANTHROPIC = "claude-sonnet-4-6"
QUIZ_GEN_PROMPT_VARIANT = "quizgen-v1"

# Up to 2 retries on validation failure (3 attempts total). Malformed JSON or a
# schema-invalid question is re-requested rather than returned to the caller.
QUIZ_GEN_RETRIES = 2

# Exact system prompt from blueprint §5 (Quiz Generator), with {n}, {lang},
# {difficulty}, and {retrieved_chunks_with_indices} placeholders preserved.
QUIZ_GEN_PROMPT_TEMPLATE = """\
You are a quiz designer. From the <material>, generate exactly {n} questions in {lang} at {difficulty} level.

Output strictly valid JSON matching this schema (no prose, no markdown):
{{
  "questions": [
    {{
      "type": "mcq" | "open",
      "prompt": str,
      "options": [str,str,str,str] | null,
      "correct_answer": str,
      "rationale": str,
      "source_chunk_ids": [int]
    }}
  ]
}}

Rules:
- ~70% MCQ, ~30% open-ended.
- Each MCQ has exactly 4 options, exactly one correct; distractors must be plausible misconceptions, not absurd.
- Rationale must cite chunk ids.
- No questions answerable without the material.
- Calibrate difficulty: easy = recall; medium = apply; hard = analyze/evaluate.
- Reply in {lang} (the same script as the source where applicable).

<material>
{retrieved_chunks_with_indices}
</material>"""


class QuizQuestion(BaseModel):
    type: Literal["mcq", "open"]
    prompt: str
    options: list[str] | None
    correct_answer: str
    rationale: str
    source_chunk_ids: list[int]

    @model_validator(mode="after")
    def _validate_shape(self) -> "QuizQuestion":
        if self.type == "mcq":
            if self.options is None or len(self.options) != 4:
                raise ValueError("mcq questions must have exactly 4 options")
            if self.correct_answer not in self.options:
                raise ValueError("mcq correct_answer must be one of the options")
        else:  # open
            if self.options is not None:
                raise ValueError("open questions must not have options")
        return self


class QuizSet(BaseModel):
    questions: list[QuizQuestion]


_quiz_gen_agent: Agent[None, QuizSet] | None = None
_quiz_gen_agent_anthropic: Agent[None, QuizSet] | None = None


def resolve_provider(provider: QuizProvider) -> QuizProvider:
    """Fall back to Anthropic when an OpenAI request has no key configured.

    Lets quiz generation "just work" with whichever key is set: the web router
    asks for "openai" but transparently uses Claude when OPENAI_API_KEY is empty.
    """
    from ..settings import settings

    if provider == "openai" and not settings.openai_api_key:
        return "anthropic"
    return provider


def get_quiz_gen_agent(provider: QuizProvider = "openai") -> Agent[None, QuizSet]:
    if resolve_provider(provider) == "anthropic":
        return _get_quiz_gen_agent_anthropic()
    global _quiz_gen_agent
    if _quiz_gen_agent is None:
        from ..settings import settings
        model = OpenAIChatModel(
            QUIZ_GEN_MODEL,
            provider=OpenAIProvider(api_key=settings.openai_api_key),
        )
        _quiz_gen_agent = Agent(
            model,
            output_type=QuizSet,
            retries=QUIZ_GEN_RETRIES,
        )
    return _quiz_gen_agent


def _get_quiz_gen_agent_anthropic() -> Agent[None, QuizSet]:
    global _quiz_gen_agent_anthropic
    if _quiz_gen_agent_anthropic is None:
        from ..settings import settings
        model = AnthropicModel(
            QUIZ_GEN_MODEL_ANTHROPIC,
            provider=AnthropicProvider(api_key=settings.anthropic_api_key),
        )
        _quiz_gen_agent_anthropic = Agent(
            model,
            output_type=QuizSet,
            retries=QUIZ_GEN_RETRIES,
        )
    return _quiz_gen_agent_anthropic


def build_quiz_gen_prompt(
    n: int,
    lang: str,
    difficulty: str,
    sources_block: str,
) -> str:
    return QUIZ_GEN_PROMPT_TEMPLATE.format(
        n=n,
        lang=lang,
        difficulty=difficulty,
        retrieved_chunks_with_indices=sources_block,
    )


async def generate_quiz(
    n: int,
    lang: str,
    difficulty: str,
    sources_block: str,
    provider: QuizProvider = "openai",
) -> QuizSet:
    prompt = build_quiz_gen_prompt(n, lang, difficulty, sources_block)
    result = await get_quiz_gen_agent(provider).run(prompt)
    return result.output
