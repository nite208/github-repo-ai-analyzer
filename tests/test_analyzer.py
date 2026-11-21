import json
from unittest.mock import MagicMock
import pytest
from src.analyzer import analyze_repository
from src.exceptions import LlmAnalysisError
from src.metrics import RepoMetrics
from src.repo_collector import RepoData


def create_sample_repo_data() -> RepoData:
    metrics = RepoMetrics(
        has_tests=True,
        has_ci=True,
        has_license=True,
        has_contributing=True,
        has_readme=True,
        readme_length=500,
        total_files=10,
        top_level_directories=["src", "tests"],
        language_percentages={"Python": 100.0},
    )
    return RepoData(
        owner="psf",
        repo="requests",
        metadata={"name": "requests"},
        languages={"Python": 1000},
        readme="# Requests",
        tree_paths=["src/api.py", "tests/test_api.py"],
        tree_truncated=False,
        package_descriptors={},
        good_first_issues=[],
        metrics=metrics,
    )


def test_analyzer_succeeds_first_attempt() -> None:
    valid_payload = {
        "executive_summary": "High quality HTTP library.",
        "tech_stack": ["Python"],
        "strengths": ["Readable API"],
        "architecture_and_organization": "Modular architecture.",
        "recommendations": [
            {"title": "Rec 1", "rationale": "Rat 1", "priority": "high"},
            {"title": "Rec 2", "rationale": "Rat 2", "priority": "medium"},
            {"title": "Rec 3", "rationale": "Rat 3", "priority": "low"},
        ],
        "contribution_opportunities": ["First issue"],
    }
    mock_llm = MagicMock()
    mock_llm.generate_completion.return_value = json.dumps(valid_payload)

    repo_data = create_sample_repo_data()
    analysis = analyze_repository(repo_data, mock_llm)

    assert mock_llm.generate_completion.call_count == 1
    assert len(analysis.recommendations) == 3
    assert analysis.recommendations[0].title == "Rec 1"


def test_analyzer_retries_and_succeeds_on_second_attempt() -> None:
    bad_payload = "not json at all"
    valid_payload = {
        "executive_summary": "Recovered analysis.",
        "tech_stack": ["Python"],
        "strengths": ["Reliable"],
        "architecture_and_organization": "Clean layout.",
        "recommendations": [
            {"title": "Fix 1", "rationale": "Reason 1", "priority": "high"},
            {"title": "Fix 2", "rationale": "Reason 2", "priority": "medium"},
            {"title": "Fix 3", "rationale": "Reason 3", "priority": "low"},
        ],
        "contribution_opportunities": [],
    }

    mock_llm = MagicMock()
    mock_llm.generate_completion.side_effect = [bad_payload, json.dumps(valid_payload)]

    repo_data = create_sample_repo_data()
    analysis = analyze_repository(repo_data, mock_llm)

    assert mock_llm.generate_completion.call_count == 2
    assert analysis.executive_summary == "Recovered analysis."


def test_analyzer_fails_after_retry() -> None:
    bad_payload = "invalid json response"
    mock_llm = MagicMock()
    mock_llm.generate_completion.side_effect = [bad_payload, bad_payload]

    repo_data = create_sample_repo_data()
    with pytest.raises(LlmAnalysisError):
        analyze_repository(repo_data, mock_llm)

    assert mock_llm.generate_completion.call_count == 2
