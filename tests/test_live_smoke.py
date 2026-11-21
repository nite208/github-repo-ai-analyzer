import os
import pytest
from src.analyzer import analyze_repository
from src.exceptions import GitHubNotFoundError, InvalidRepoUrlError
from src.github_client import GitHubClient
from src.llm_client import LLMClient
from src.repo_collector import collect_repository_data
from src.url_parser import parse_github_url

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        os.environ.get("RUN_LIVE") != "1",
        reason="Skipped unless RUN_LIVE=1",
    ),
]


def test_live_smoke_collect_and_analyze_requests() -> None:
    owner, repo = parse_github_url("psf/requests")
    client = GitHubClient()
    repo_data = collect_repository_data(client, owner, repo)

    assert repo_data.metadata.get("name") == "requests"
    assert repo_data.readme is not None and len(repo_data.readme) > 0

    from src.config import GROQ_API_KEY
    if not GROQ_API_KEY:
        pytest.skip("GROQ_API_KEY is not set in environment or .env")

    llm_client = LLMClient()
    analysis = analyze_repository(repo_data, llm_client)

    assert len(analysis.recommendations) >= 3
    assert analysis.executive_summary
    assert len(analysis.tech_stack) > 0


def test_live_smoke_non_existent_repository() -> None:
    client = GitHubClient()
    with pytest.raises(GitHubNotFoundError):
        collect_repository_data(client, "nonexistent-user-98741", "nonexistent-repo-65412")


def test_live_smoke_garbage_input() -> None:
    with pytest.raises(InvalidRepoUrlError):
        parse_github_url("https://gitlab.com/unknown/repo")
