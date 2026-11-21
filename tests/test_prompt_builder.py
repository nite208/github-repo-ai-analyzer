from src.prompt_builder import (
    build_analysis_prompt,
    truncate_file_list,
    truncate_text,
)


def test_truncate_text_within_budget() -> None:
    text = "Short README content."
    result = truncate_text(text, budget=100)
    assert result == text


def test_truncate_text_exceeding_budget() -> None:
    text = "A" * 500
    budget = 100
    result = truncate_text(text, budget=budget)
    assert len(result) <= budget
    assert "...[truncated for length]..." in result


def test_truncate_file_list() -> None:
    paths = [f"path/to/module_{i}.py" for i in range(100)]
    budget = 200
    result = truncate_file_list(paths, budget=budget)
    assert len(result) <= budget + 50
    assert "...[remaining paths truncated]..." in result


def test_build_analysis_prompt_truncation() -> None:
    metadata = {"name": "sample-repo"}
    languages = {"Python": 1000}
    long_readme = "R" * 2000
    long_paths = [f"src/file_{i}.py" for i in range(200)]

    prompt = build_analysis_prompt(
        metadata=metadata,
        languages=languages,
        readme_content=long_readme,
        tree_paths=long_paths,
        package_descriptors={},
        good_first_issues=[],
        readme_budget=150,
        file_tree_budget=100,
    )

    assert "...[truncated for length]..." in prompt
    assert "...[remaining paths truncated]..." in prompt
    assert "sample-repo" in prompt
