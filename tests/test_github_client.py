import base64
from unittest.mock import MagicMock, patch
import pytest
import requests
from src.exceptions import (
    GitHubNetworkError,
    GitHubNotFoundError,
    GitHubRateLimitError,
)
from src.github_client import GitHubClient


def test_200_repository_fetch() -> None:
    client = GitHubClient(token=None, user_agent="CustomAgent/1.0")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"X-RateLimit-Remaining": "50"}
    mock_resp.json.return_value = {
        "name": "requests",
        "full_name": "psf/requests",
        "description": "Python HTTP for Humans.",
        "stargazers_count": 50000,
        "forks_count": 9000,
        "watchers_count": 50000,
        "language": "Python",
        "license": {"spdx_id": "Apache-2.0"},
        "topics": ["python", "http"],
        "open_issues_count": 120,
        "default_branch": "main",
        "created_at": "2011-02-13T18:38:17Z",
        "pushed_at": "2024-01-01T00:00:00Z",
        "size": 12345,
    }

    with patch("requests.get", return_value=mock_resp):
        data = client.get_repository("psf", "requests")

    assert data["name"] == "requests"
    assert data["stars"] == 50000
    assert data["primary_language"] == "Python"
    assert data["license"] == "Apache-2.0"


def test_404_not_found() -> None:
    client = GitHubClient()
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.headers = {}

    with patch("requests.get", return_value=mock_resp):
        with pytest.raises(GitHubNotFoundError):
            client.get_repository("nonexistent", "nowhere")


def test_403_rate_limit() -> None:
    client = GitHubClient()
    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_resp.headers = {
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": "1730000000",
    }
    mock_resp.text = "API rate limit exceeded"

    with patch("requests.get", return_value=mock_resp):
        with pytest.raises(GitHubRateLimitError) as exc_info:
            client.get_repository("psf", "requests")

    assert exc_info.value.reset_timestamp == 1730000000


def test_429_rate_limit() -> None:
    client = GitHubClient()
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.headers = {"X-RateLimit-Reset": "1730000100"}

    with patch("requests.get", return_value=mock_resp):
        with pytest.raises(GitHubRateLimitError):
            client.get_repository("psf", "requests")


def test_timeout_and_connection_error() -> None:
    client = GitHubClient()
    with patch("requests.get", side_effect=requests.exceptions.Timeout("timed out")):
        with pytest.raises(GitHubNetworkError):
            client.get_repository("psf", "requests")

    with patch("requests.get", side_effect=requests.exceptions.ConnectionError("conn failed")):
        with pytest.raises(GitHubNetworkError):
            client.get_repository("psf", "requests")


def test_user_agent_header_sent_on_every_call() -> None:
    client = GitHubClient(user_agent="TestAgent/2.0")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {}
    mock_resp.json.return_value = {}

    with patch("requests.get", return_value=mock_resp) as mock_get:
        client.get_repository("psf", "requests")
        headers = mock_get.call_args.kwargs["headers"]
        assert headers["User-Agent"] == "TestAgent/2.0"


def test_token_header_only_when_configured() -> None:
    client_without_token = GitHubClient(token=None)
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {}
    mock_resp.json.return_value = {}

    with patch("requests.get", return_value=mock_resp) as mock_get:
        client_without_token.get_repository("psf", "requests")
        headers = mock_get.call_args.kwargs["headers"]
        assert "Authorization" not in headers

    client_with_token = GitHubClient(token="mock_token_abc")
    with patch("requests.get", return_value=mock_resp) as mock_get:
        client_with_token.get_repository("psf", "requests")
        headers = mock_get.call_args.kwargs["headers"]
        assert headers["Authorization"] == "Bearer mock_token_abc"


def test_readme_base64_decoding() -> None:
    client = GitHubClient()
    text = "Hello GitHub Readme!"
    encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {}
    mock_resp.json.return_value = {"content": encoded, "encoding": "base64"}

    with patch("requests.get", return_value=mock_resp):
        decoded = client.get_readme("psf", "requests")

    assert decoded == text


def test_tree_truncation_handling() -> None:
    client = GitHubClient()
    mock_resp_truncated = MagicMock()
    mock_resp_truncated.status_code = 200
    mock_resp_truncated.headers = {}
    mock_resp_truncated.json.return_value = {
        "truncated": True,
        "tree": [{"path": "file1.py"}, {"path": "file2.py"}],
    }

    with patch("requests.get", return_value=mock_resp_truncated):
        paths, truncated = client.get_tree("psf", "requests", "main")
        assert truncated is True
        assert paths == ["file1.py", "file2.py"]

    mock_resp_clean = MagicMock()
    mock_resp_clean.status_code = 200
    mock_resp_clean.headers = {}
    mock_resp_clean.json.return_value = {
        "truncated": False,
        "tree": [{"path": "file1.py"}],
    }

    with patch("requests.get", return_value=mock_resp_clean):
        paths, truncated = client.get_tree("psf", "requests", "main")
        assert truncated is False
        assert paths == ["file1.py"]
