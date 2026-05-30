import pytest
from pydantic import ValidationError

from app.agents.planner import (
    LearningPlan,
    PlanDay,
    PlanTask,
    build_planner_prompt,
)


class TestPlanModels:
    def test_valid_task(self) -> None:
        t = PlanTask(
            type="read",
            title="3-bobni o'qish",
            estimated_minutes=20,
            material_id=None,
            gap_topic="Fotosintez",
        )
        assert t.type == "read"

    def test_rejects_invalid_task_type(self) -> None:
        with pytest.raises(ValidationError):
            PlanTask(
                type="watch",  # type: ignore[arg-type]
                title="x",
                estimated_minutes=10,
                material_id=None,
                gap_topic=None,
            )

    def test_learning_plan_parses(self) -> None:
        plan = LearningPlan(
            plan=[
                PlanDay(
                    date="2026-05-31",
                    tasks=[
                        PlanTask(
                            type="quiz",
                            title="Mini test",
                            estimated_minutes=15,
                            material_id=None,
                            gap_topic=None,
                        )
                    ],
                )
            ]
        )
        assert plan.plan[0].date == "2026-05-31"


class TestBuildPlannerPrompt:
    def test_fills_placeholders_and_keeps_rules(self) -> None:
        prompt = build_planner_prompt(
            minutes_per_day=30,
            target_date="2026-06-07",
            lang="uz-latn",
            gaps_json='[{"topic":"Fotosintez","severity":4}]',
        )
        assert "available daily time (30 min)" in prompt
        assert "target date (2026-06-07)" in prompt
        assert "language uz-latn" in prompt
        assert "Apply spaced repetition: re-review on days 1, 3, 7, 14 after first encounter." in prompt
        assert "Final 2 days = full mock quiz + review." in prompt
        assert '"Fotosintez"' in prompt
        assert "<gaps>" in prompt and "</gaps>" in prompt
        # No unfilled placeholders.
        assert "{minutes_per_day}" not in prompt
        assert "{target_date}" not in prompt
        assert "{lang}" not in prompt
