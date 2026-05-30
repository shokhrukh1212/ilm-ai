from typing import Literal

from pydantic import BaseModel, model_validator
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

QUIZ_GEN_MODEL = "gpt-4o"
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


def get_quiz_gen_agent() -> Agent[None, QuizSet]:
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
) -> QuizSet:
    prompt = build_quiz_gen_prompt(n, lang, difficulty, sources_block)
    result = await get_quiz_gen_agent().run(prompt)
    return result.output
