from dataclasses import dataclass
import logging
from typing import Any
from src.github_client import GitHubClient
from src.metrics import RepoMetrics, compute_repo_metrics

logger = logging.getLogger(__name__)

ROOT_DESCRIPTORS = [
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "setup.py",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
]


@dataclass
class RepoData:
    owner: str
    repo: str
    metadata: dict[str, Any]
    languages: dict[str, int]
    readme: str | None
    tree_paths: list[str]
    tree_truncated: bool
    package_descriptors: dict[str, str]
    good_first_issues: list[dict[str, Any]]
    metrics: RepoMetrics


def collect_repository_data(
    client: GitHubClient, owner: str, repo: str
) -> RepoData:
    logger.info("Collecting repository data for %s/%s", owner, repo)
    metadata = client.get_repository(owner, repo)
    languages = client.get_languages(owner, repo)
    readme = client.get_readme(owner, repo)

    default_branch = str(metadata.get("default_branch", "main"))
    tree_paths, tree_truncated = client.get_tree(owner, repo, default_branch)

    descriptors: dict[str, str] = {}
    path_set = set(tree_paths)
    for desc_name in ROOT_DESCRIPTORS:
        if desc_name in path_set:
            content = client.get_file_content(owner, repo, desc_name)
            if content:
                descriptors[desc_name] = content

    issues = client.get_good_first_issues(owner, repo)
    metrics = compute_repo_metrics(tree_paths, readme, languages)

    return RepoData(
        owner=owner,
        repo=repo,
        metadata=metadata,
        languages=languages,
        readme=readme,
        tree_paths=tree_paths,
        tree_truncated=tree_truncated,
        package_descriptors=descriptors,
        good_first_issues=issues,
        metrics=metrics,
    )
