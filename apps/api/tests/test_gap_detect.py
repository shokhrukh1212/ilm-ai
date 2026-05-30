import pytest
from pydantic import ValidationError

from app.agents.gap_detect import (
    GAP_DETECT_SYSTEM_PROMPT,
    GapSet,
    KnowledgeGapOut,
)


class TestKnowledgeGapOut:
    def test_valid(self) -> None:
        g = KnowledgeGapOut(
            topic="Hujayra nafas olishi",
            severity=3,
            evidence_question_ids=[1, 2],
            suggested_review="14-18 betlarni qayta o'qing",
        )
        assert g.severity == 3

    def test_rejects_severity_zero(self) -> None:
        with pytest.raises(ValidationError):
            KnowledgeGapOut(
                topic="t", severity=0, evidence_question_ids=[], suggested_review="r"
            )

    def test_rejects_severity_six(self) -> None:
        with pytest.raises(ValidationError):
            KnowledgeGapOut(
                topic="t", severity=6, evidence_question_ids=[], suggested_review="r"
            )


class TestGapSet:
    def test_parses(self) -> None:
        gs = GapSet(
            gaps=[
                KnowledgeGapOut(
                    topic="t", severity=2, evidence_question_ids=[5], suggested_review="r"
                )
            ]
        )
        assert len(gs.gaps) == 1


class TestSystemPrompt:
    def test_contains_blueprint_rules(self) -> None:
        assert "Cluster wrong answers by topic, not by question." in GAP_DETECT_SYSTEM_PROMPT
        assert "severity = round((wrong_count_in_topic / total_in_topic) * 5)." in GAP_DETECT_SYSTEM_PROMPT
        assert "Max 5 gaps; merge similar ones." in GAP_DETECT_SYSTEM_PROMPT
