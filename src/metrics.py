from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class RepoMetrics:
    has_tests: bool
    has_ci: bool
    has_license: bool
    has_contributing: bool
    has_readme: bool
    readme_length: int
    total_files: int
    top_level_directories: list[str]
    language_percentages: dict[str, float]


def calculate_language_percentages(
    languages: dict[str, int]
) -> dict[str, float]:
    total_bytes = sum(languages.values())
    if total_bytes == 0:
        return {}
    return {
        lang: round((count / total_bytes) * 100, 2)
        for lang, count in languages.items()
    }


def extract_top_level_dirs(paths: list[str]) -> list[str]:
    dirs = set()
    for path in paths:
        parts = path.split("/")
        if len(parts) > 1 and parts[0]:
            dirs.add(parts[0])
    return sorted(list(dirs))


def check_tests_present(paths: list[str]) -> bool:
    for path in paths:
        lower = path.lower()
        if lower.startswith(("test/", "tests/", "spec/")):
            return True
        if "/test/" in lower or "/tests/" in lower:
            return True
        if lower.endswith(
            ("_test.py", "test_.py", ".test.js", ".spec.js", ".test.ts", "_test.go")
        ):
            return True
    return False


def check_ci_present(paths: list[str]) -> bool:
    for path in paths:
        lower = path.lower()
        if lower.startswith(".github/workflows/"):
            return True
        if lower in (".gitlab-ci.yml", ".travis.yml", "azure-pipelines.yml"):
            return True
    return False


def check_license_present(paths: list[str]) -> bool:
    for path in paths:
        base = path.split("/")[-1].upper()
        if base.startswith("LICENSE") or base.startswith("COPYING"):
            return True
    return False


def check_contributing_present(paths: list[str]) -> bool:
    for path in paths:
        base = path.split("/")[-1].upper()
        if base.startswith("CONTRIBUTING"):
            return True
    return False


def compute_repo_metrics(
    paths: list[str],
    readme_content: str | None,
    languages: dict[str, int],
) -> RepoMetrics:
    logger.info("Computing metrics for %d paths", len(paths))
    has_readme = bool(readme_content and len(readme_content.strip()) > 0)
    readme_length = len(readme_content) if readme_content else 0

    return RepoMetrics(
        has_tests=check_tests_present(paths),
        has_ci=check_ci_present(paths),
        has_license=check_license_present(paths),
        has_contributing=check_contributing_present(paths),
        has_readme=has_readme,
        readme_length=readme_length,
        total_files=len(paths),
        top_level_directories=extract_top_level_dirs(paths),
        language_percentages=calculate_language_percentages(languages),
    )
