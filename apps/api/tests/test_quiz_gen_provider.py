import pytest
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openai import OpenAIChatModel

from app.agents import quiz_gen
from app.settings import settings


@pytest.fixture
def dummy_openai_key(monkeypatch: pytest.MonkeyPatch) -> None:
    # OpenAIProvider requires a non-empty key to construct the model.
    monkeypatch.setattr(settings, "openai_api_key", "sk-test")
    monkeypatch.setattr(quiz_gen, "_quiz_gen_agent", None)


class TestQuizGenProvider:
    def test_anthropic_agent_uses_claude(self) -> None:
        agent = quiz_gen.get_quiz_gen_agent("anthropic")
        assert isinstance(agent.model, AnthropicModel)

    def test_default_agent_uses_openai(self, dummy_openai_key: None) -> None:
        agent = quiz_gen.get_quiz_gen_agent("openai")
        assert isinstance(agent.model, OpenAIChatModel)

    def test_anthropic_cached(self) -> None:
        assert quiz_gen.get_quiz_gen_agent("anthropic") is quiz_gen.get_quiz_gen_agent(
            "anthropic"
        )

    def test_openai_and_anthropic_distinct(self, dummy_openai_key: None) -> None:
        assert quiz_gen.get_quiz_gen_agent("openai") is not quiz_gen.get_quiz_gen_agent(
            "anthropic"
        )

    def test_falls_back_to_anthropic_without_openai_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "openai_api_key", "")
        assert quiz_gen.resolve_provider("openai") == "anthropic"
        agent = quiz_gen.get_quiz_gen_agent("openai")
        assert isinstance(agent.model, AnthropicModel)

    def test_keeps_openai_when_key_present(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(settings, "openai_api_key", "sk-test")
        assert quiz_gen.resolve_provider("openai") == "openai"

    def test_build_prompt_includes_sources(self) -> None:
        prompt = quiz_gen.build_quiz_gen_prompt(5, "uz-latn", "medium", "[chunk 1] hi")
        assert "[chunk 1] hi" in prompt
        assert "uz-latn" in prompt
