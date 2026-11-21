from src.metrics import (
    calculate_language_percentages,
    compute_repo_metrics,
    extract_top_level_dirs,
)


def test_calculate_language_percentages() -> None:
    languages = {"Python": 800, "HTML": 200}
    res = calculate_language_percentages(languages)
    assert res["Python"] == 80.0
    assert res["HTML"] == 20.0

    empty = calculate_language_percentages({})
    assert empty == {}


def test_extract_top_level_dirs() -> None:
    paths = [
        "src/main.py",
        "src/utils.py",
        "tests/test_main.py",
        "docs/index.md",
        "README.md",
        "package.json",
    ]
    dirs = extract_top_level_dirs(paths)
    assert dirs == ["docs", "src", "tests"]


def test_compute_repo_metrics_full() -> None:
    paths = [
        ".github/workflows/ci.yml",
        "src/app.py",
        "tests/test_app.py",
        "LICENSE.md",
        "CONTRIBUTING.md",
        "README.md",
    ]
    readme = "# Project Name\nDocumentation content here."
    languages = {"Python": 1000}

    metrics = compute_repo_metrics(paths, readme, languages)

    assert metrics.has_tests is True
    assert metrics.has_ci is True
    assert metrics.has_license is True
    assert metrics.has_contributing is True
    assert metrics.has_readme is True
    assert metrics.readme_length == len(readme)
    assert metrics.total_files == 6
    assert ".github" in metrics.top_level_directories
    assert "src" in metrics.top_level_directories
    assert metrics.language_percentages == {"Python": 100.0}


def test_compute_repo_metrics_empty_or_minimal() -> None:
    paths = ["main.py"]
    metrics = compute_repo_metrics(paths, readme_content=None, languages={})

    assert metrics.has_tests is False
    assert metrics.has_ci is False
    assert metrics.has_license is False
    assert metrics.has_contributing is False
    assert metrics.has_readme is False
    assert metrics.readme_length == 0
    assert metrics.total_files == 1
    assert metrics.top_level_directories == []
    assert metrics.language_percentages == {}
