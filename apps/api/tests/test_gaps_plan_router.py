import json
from datetime import date, datetime

import pytest
from pydantic import ValidationError

from app.routers.gaps import _row_to_gap
from app.routers.plan import (
    GeneratePlanRequest,
    ToggleTaskRequest,
    _parse_plan_jsonb,
    _suggested_review,
)
from app.services.gap_detection import _dominant_material, _normalize


class TestGeneratePlanRequest:
    def test_defaults_target_date_optional(self) -> None:
        req = GeneratePlanRequest(minutes_per_day=20)
        assert req.target_date is None

    def test_accepts_target_date(self) -> None:
        req = GeneratePlanRequest(minutes_per_day=20, target_date=date(2026, 6, 7))
        assert req.target_date == date(2026, 6, 7)

    def test_rejects_too_few_minutes(self) -> None:
        with pytest.raises(ValidationError):
            GeneratePlanRequest(minutes_per_day=4)

    def test_rejects_too_many_minutes(self) -> None:
        with pytest.raises(ValidationError):
            GeneratePlanRequest(minutes_per_day=241)


class TestToggleTaskRequest:
    def test_valid(self) -> None:
        req = ToggleTaskRequest(date="2026-05-31", task_index=0, done=True)
        assert req.done is True

    def test_rejects_negative_index(self) -> None:
        with pytest.raises(ValidationError):
            ToggleTaskRequest(date="2026-05-31", task_index=-1, done=True)


class TestParsePlanJsonb:
    def test_none(self) -> None:
        assert _parse_plan_jsonb(None) == []

    def test_dict_with_plan(self) -> None:
        assert _parse_plan_jsonb({"plan": [{"date": "d", "tasks": []}]}) == [
            {"date": "d", "tasks": []}
        ]

    def test_json_string(self) -> None:
        raw = json.dumps({"plan": [{"date": "d", "tasks": []}]})
        assert _parse_plan_jsonb(raw) == [{"date": "d", "tasks": []}]


class TestSuggestedReview:
    def test_from_dict(self) -> None:
        assert _suggested_review({"suggested_review": "re-read"}) == "re-read"

    def test_from_json_string(self) -> None:
        assert _suggested_review(json.dumps({"suggested_review": "x"})) == "x"

    def test_none(self) -> None:
        assert _suggested_review(None) is None


class TestRowToGap:
    def test_parses_string_evidence(self) -> None:
        gap = _row_to_gap(
            {
                "id": 1,
                "topic": "Fotosintez",
                "severity": 4,
                "material_id": None,
                "evidence": json.dumps({"question_ids": [1, 2], "suggested_review": "r"}),
                "status": "open",
                "created_at": datetime(2026, 5, 30, 12, 0, 0),
            }
        )
        assert gap.evidence == {"question_ids": [1, 2], "suggested_review": "r"}
        assert gap.severity == 4


class TestDominantMaterial:
    def test_picks_most_common(self) -> None:
        material_by_question = {1: "mat-a", 2: "mat-a", 3: "mat-b"}
        assert _dominant_material([1, 2, 3], material_by_question) == "mat-a"

    def test_none_when_no_match(self) -> None:
        assert _dominant_material([99], {1: "mat-a"}) is None


class TestNormalize:
    def test_trims_and_lowercases(self) -> None:
        assert _normalize("  Hujayra Nafas  ") == "hujayra nafas"
