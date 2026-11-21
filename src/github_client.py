import base64
import logging
from typing import Any
import requests
from src.config import GITHUB_TOKEN, USER_AGENT
from src.exceptions import (
    GitHubApiError,
    GitHubNetworkError,
    GitHubNotFoundError,
    GitHubRateLimitError,
)

logger = logging.getLogger(__name__)


class GitHubClient:
    def __init__(
        self,
        token: str | None = GITHUB_TOKEN,
        user_agent: str = USER_AGENT,
        timeout: int = 15,
    ) -> None:
        self.token = token
        self.user_agent = user_agent
        self.timeout = timeout
        self.base_url = "https://api.github.com"

    def _build_headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": self.user_agent,
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _check_rate_limit(self, response: requests.Response) -> None:
        remaining = response.headers.get("X-RateLimit-Remaining")
        reset_ts = response.headers.get("X-RateLimit-Reset")
        reset_int = int(reset_ts) if reset_ts and reset_ts.isdigit() else None

        if response.status_code in (403, 429) and remaining == "0":
            msg = (
                f"GitHub API rate limit exceeded. Resets at timestamp {reset_int}. "
                "Add a GITHUB_TOKEN to increase limits."
            )
            raise GitHubRateLimitError(msg, reset_timestamp=reset_int)
        if response.status_code == 429:
            msg = "Too many requests to GitHub API. Please wait and try again."
            raise GitHubRateLimitError(msg, reset_timestamp=reset_int)

    def _request(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        logger.debug("Requesting GitHub API URL: %s", url)
        try:
            resp = requests.get(
                url,
                headers=self._build_headers(),
                params=params,
                timeout=self.timeout,
            )
        except requests.exceptions.Timeout as err:
            raise GitHubNetworkError(f"Request to GitHub timed out: {err}") from err
        except requests.exceptions.ConnectionError as err:
            raise GitHubNetworkError(f"Connection error reaching GitHub: {err}") from err
        except requests.exceptions.RequestException as err:
            raise GitHubNetworkError(f"Network error: {err}") from err

        self._check_rate_limit(resp)

        if resp.status_code == 404:
            raise GitHubNotFoundError(
                f"Resource not found at {endpoint}", status_code=404
            )
        if resp.status_code >= 400:
            raise GitHubApiError(
                f"GitHub API error {resp.status_code}: {resp.text}",
                status_code=resp.status_code,
            )
        return resp

    def get_repository(self, owner: str, repo: str) -> dict[str, Any]:
        resp = self._request(f"/repos/{owner}/{repo}")
        data = resp.json()
        return {
            "name": data.get("name", ""),
            "full_name": data.get("full_name", f"{owner}/{repo}"),
            "description": data.get("description") or "",
            "stars": data.get("stargazers_count", 0),
            "forks": data.get("forks_count", 0),
            "watchers": data.get("watchers_count", 0),
            "primary_language": data.get("language") or "Unknown",
            "license": data.get("license", {}).get("spdx_id")
            if data.get("license")
            else None,
            "topics": data.get("topics", []),
            "open_issues_count": data.get("open_issues_count", 0),
            "default_branch": data.get("default_branch", "main"),
            "created_at": data.get("created_at", ""),
            "pushed_at": data.get("pushed_at", ""),
            "size_kb": data.get("size", 0),
        }

    def get_languages(self, owner: str, repo: str) -> dict[str, int]:
        resp = self._request(f"/repos/{owner}/{repo}/languages")
        return resp.json()

    def get_readme(self, owner: str, repo: str) -> str | None:
        try:
            resp = self._request(f"/repos/{owner}/{repo}/readme")
            content_b64 = resp.json().get("content", "")
            return base64.b64decode(content_b64.encode("ascii")).decode(
                "utf-8", errors="replace"
            )
        except GitHubNotFoundError:
            logger.info("No README found for %s/%s", owner, repo)
            return None

    def get_tree(
        self, owner: str, repo: str, default_branch: str
    ) -> tuple[list[str], bool]:
        resp = self._request(
            f"/repos/{owner}/{repo}/git/trees/{default_branch}",
            params={"recursive": "1"},
        )
        data = resp.json()
        is_truncated = bool(data.get("truncated", False))
        if is_truncated:
            logger.warning("Tree for %s/%s is truncated", owner, repo)
        items = data.get("tree", [])
        paths = [item["path"] for item in items if "path" in item]
        return paths, is_truncated

    def get_file_content(self, owner: str, repo: str, path: str) -> str | None:
        try:
            resp = self._request(f"/repos/{owner}/{repo}/contents/{path}")
            content_b64 = resp.json().get("content", "")
            return base64.b64decode(content_b64.encode("ascii")).decode(
                "utf-8", errors="replace"
            )
        except GitHubNotFoundError:
            return None

    def get_good_first_issues(
        self, owner: str, repo: str
    ) -> list[dict[str, Any]]:
        try:
            resp = self._request(
                f"/repos/{owner}/{repo}/issues",
                params={"labels": "good first issue", "state": "open", "per_page": "10"},
            )
            raw = resp.json()
        except GitHubApiError:
            return []

        clean_issues: list[dict[str, Any]] = []
        for issue in raw:
            if "pull_request" in issue:
                continue
            clean_issues.append(
                {
                    "number": issue.get("number"),
                    "title": issue.get("title", ""),
                    "url": issue.get("html_url", ""),
                    "comments": issue.get("comments", 0),
                }
            )
            if len(clean_issues) >= 5:
                break
        return clean_issues
