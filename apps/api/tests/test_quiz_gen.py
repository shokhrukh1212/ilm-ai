import pytest
from pydantic import ValidationError

from app.agents.quiz_gen import (
    QUIZ_GEN_RETRIES,
    QuizQuestion,
    QuizSet,
    build_quiz_gen_prompt,
)
from app.services.quiz_sources import _even_sample, build_sources_block
from app.services.retrieve import RetrievedChunk


def _chunk(chunk_id: int, page: int | None = 1) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        content=f"content-{chunk_id}",
        page=page,
        material_id="mat-1",
        score=0.0,
    )


class TestQuizQuestionValidation:
    def test_valid_mcq(self) -> None:
        q = QuizQuestion(
            type="mcq",
            prompt="2+2?",
            options=["3", "4", "5", "6"],
            correct_answer="4",
            rationale="see chunk 1",
            source_chunk_ids=[1],
        )
        assert q.correct_answer == "4"

    def test_mcq_requires_four_options(self) -> None:
        with pytest.raises(ValidationError):
            QuizQuestion(
                type="mcq",
                prompt="?",
                options=["a", "b", "c"],
                correct_answer="a",
                rationale="r",
                source_chunk_ids=[1],
            )

    def test_mcq_correct_answer_must_be_in_options(self) -> None:
        with pytest.raises(ValidationError):
            QuizQuestion(
                type="mcq",
                prompt="?",
                options=["a", "b", "c", "d"],
                correct_answer="z",
                rationale="r",
                source_chunk_ids=[1],
            )

    def test_open_must_not_have_options(self) -> None:
        with pytest.raises(ValidationError):
            QuizQuestion(
                type="open",
                prompt="Explain.",
                options=["a", "b", "c", "d"],
                correct_answer="...",
                rationale="r",
                source_chunk_ids=[1],
            )

    def test_valid_open(self) -> None:
        q = QuizQuestion(
            type="open",
            prompt="Explain photosynthesis.",
            options=None,
            correct_answer="Plants convert light to energy.",
            rationale="chunk 2",
            source_chunk_ids=[2],
        )
        assert q.options is None


class TestQuizSet:
    def test_parses_list(self) -> None:
        qs = QuizSet(
            questions=[
                QuizQuestion(
                    type="open",
                    prompt="Q",
                    options=None,
                    correct_answer="A",
                    rationale="r",
                    source_chunk_ids=[1],
                )
            ]
        )
        assert len(qs.questions) == 1


class TestBuildQuizGenPrompt:
    def test_fills_placeholders_and_keeps_rules(self) -> None:
        prompt = build_quiz_gen_prompt(10, "uz-latn", "medium", "[chunk 5] hello")
        assert "exactly 10 questions in uz-latn at medium level" in prompt
        assert "~70% MCQ, ~30% open-ended." in prompt
        assert "[chunk 5] hello" in prompt
        assert "<material>" in prompt and "</material>" in prompt
        # No unfilled placeholders should remain.
        assert "{n}" not in prompt
        assert "{retrieved_chunks_with_indices}" not in prompt

    def test_retries_is_two(self) -> None:
        assert QUIZ_GEN_RETRIES == 2


class TestSources:
    def test_build_sources_block_labels_by_chunk_id(self) -> None:
        block = build_sources_block([_chunk(42, page=7), _chunk(99, page=None)])
        assert "[chunk 42] (p.7) content-42" in block
        assert "[chunk 99] content-99" in block

    def test_even_sample_caps_and_spreads(self) -> None:
        chunks = [_chunk(i) for i in range(100)]
        sampled = _even_sample(chunks, 10)
        assert len(sampled) == 10
        # First element preserved; stride spreads across the material.
        assert sampled[0].chunk_id == 0
        assert sampled[1].chunk_id == 10

    def test_even_sample_returns_all_when_under_cap(self) -> None:
        chunks = [_chunk(i) for i in range(5)]
        assert _even_sample(chunks, 40) == chunks
