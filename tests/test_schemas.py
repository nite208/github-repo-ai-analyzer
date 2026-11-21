import pytest
from pydantic import ValidationError
from src.schemas import Recommendation, RepoAnalysis


def test_schema_accepts_valid_payload() -> None:
    data = {
        "executive_summary": "Solid and reliable HTTP client library.",
        "tech_stack": ["Python", "urllib3"],
        "strengths": ["Clear API", "Well documented"],
        "architecture_and_organization": "Modular request and session handling.",
        "recommendations": [
            {
                "title": "Add type annotations",
                "rationale": "Improves developer experience and static typing.",
                "priority": "high",
            },
            {
                "title": "Expand async test suite",
                "rationale": "Verifies concurrency edges.",
                "priority": "medium",
            },
            {
                "title": "Update release automation",
                "rationale": "Streamlines PyPI publishing.",
                "priority": "low",
            },
        ],
        "contribution_opportunities": [
            "Tackle issue 101: Improve docstrings",
            "Tackle issue 102: Fix typing error",
        ],
    }

    analysis = RepoAnalysis.model_validate(data)
    assert len(analysis.recommendations) == 3
    assert analysis.recommendations[0].priority == "high"


def test_schema_rejects_fewer_than_three_recommendations() -> None:
    data = {
        "executive_summary": "A small utility project.",
        "tech_stack": ["Python"],
        "strengths": ["Lightweight"],
        "architecture_and_organization": "Single module layout.",
        "recommendations": [
            {
                "title": "Add unit tests",
                "rationale": "Increases test coverage.",
                "priority": "high",
            },
            {
                "title": "Setup CI workflow",
                "rationale": "Automates linting.",
                "priority": "medium",
            },
        ],
        "contribution_opportunities": [],
    }

    with pytest.raises(ValidationError):
        RepoAnalysis.model_validate(data)


def test_schema_rejects_bracketed_placeholders() -> None:
    data = {
        "executive_summary": "Architecture for [Insert Project Name].",
        "tech_stack": ["Python"],
        "strengths": ["Clean code"],
        "architecture_and_organization": "Standard layout.",
        "recommendations": [
            {"title": "Rec 1", "rationale": "Rationale 1", "priority": "high"},
            {"title": "Rec 2", "rationale": "Rationale 2", "priority": "medium"},
            {"title": "Rec 3", "rationale": "Rationale 3", "priority": "low"},
        ],
        "contribution_opportunities": [],
    }

    with pytest.raises(ValidationError):
        RepoAnalysis.model_validate(data)


def test_recommendation_invalid_priority() -> None:
    with pytest.raises(ValidationError):
        Recommendation(
            title="Update docs",
            rationale="Clarify install steps",
            priority="critical",  # type: ignore[arg-type]
        )
