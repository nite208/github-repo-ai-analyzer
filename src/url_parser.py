import logging
import re
from urllib.parse import urlparse
from src.exceptions import InvalidRepoUrlError

logger = logging.getLogger(__name__)

REPO_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")


def parse_github_url(raw_input: str) -> tuple[str, str]:
    cleaned = raw_input.strip()
    if not cleaned:
        logger.warning("Empty repository input provided")
        raise InvalidRepoUrlError("Repository input cannot be empty.")

    if "://" not in cleaned and not cleaned.startswith("github.com"):
        parts = cleaned.split("/")
        if len(parts) == 2:
            owner, repo = parts[0].strip(), parts[1].strip()
            if repo.endswith(".git"):
                repo = repo[:-4]
            if REPO_NAME_PATTERN.match(owner) and REPO_NAME_PATTERN.match(repo):
                return owner, repo
            raise InvalidRepoUrlError("Invalid characters in repository name.")
        raise InvalidRepoUrlError("Expected format 'owner/repo' or a GitHub URL.")

    if not cleaned.startswith(("http://", "https://")):
        cleaned = "https://" + cleaned

    parsed = urlparse(cleaned)
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    if host != "github.com":
        raise InvalidRepoUrlError("Only GitHub repositories are supported.")

    path_segments = [seg for seg in parsed.path.strip("/").split("/") if seg]
    if len(path_segments) < 2:
        raise InvalidRepoUrlError("GitHub URL must contain both owner and repo.")

    owner = path_segments[0].strip()
    repo = path_segments[1].strip()
    if repo.endswith(".git"):
        repo = repo[:-4]

    if not (REPO_NAME_PATTERN.match(owner) and REPO_NAME_PATTERN.match(repo)):
        raise InvalidRepoUrlError("Invalid owner or repository name in URL.")

    return owner, repo
