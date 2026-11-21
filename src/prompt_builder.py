import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def truncate_text(text: str, budget: int) -> str:
    if len(text) <= budget:
        return text
    notice = "\n...[truncated for length]..."
    allowed = max(0, budget - len(notice))
    return text[:allowed] + notice


def truncate_file_list(paths: list[str], budget: int) -> str:
    lines: list[str] = []
    current_len = 0
    for path in paths:
        line = path + "\n"
        if current_len + len(line) > budget:
            lines.append("...[remaining paths truncated]...")
            break
        lines.append(line)
        current_len += len(line)
    return "".join(lines).strip()


def build_system_prompt() -> str:
    return (
        "You are an expert software architect and technical due diligence analyst. "
        "Analyze the provided repository context and produce structured JSON output. "
        "Your response must strictly follow the required JSON schema with at least 3 actionable recommendations. "
        "Never use bracketed placeholders such as [Your Name] or [Insert Link]. Provide concrete, specific insights."
    )


def build_analysis_prompt(
    metadata: dict[str, Any],
    languages: dict[str, int],
    readme_content: str | None,
    tree_paths: list[str],
    package_descriptors: dict[str, str],
    good_first_issues: list[dict[str, Any]],
    readme_budget: int = 8000,
    file_tree_budget: int = 4000,
) -> str:
    readme_sample = truncate_text(readme_content or "No README provided.", readme_budget)
    files_sample = truncate_file_list(tree_paths, file_tree_budget)

    context = {
        "repository_metadata": metadata,
        "languages": languages,
        "readme_excerpt": readme_sample,
        "file_tree_excerpt": files_sample,
        "package_descriptors": package_descriptors,
        "good_first_issues": good_first_issues,
    }

    schema_instruction = (
        "Return a valid JSON object matching this schema:\n"
        "{\n"
        '  "executive_summary": "string",\n'
        '  "tech_stack": ["string"],\n'
        '  "strengths": ["string"],\n'
        '  "architecture_and_organization": "string",\n'
        '  "recommendations": [\n'
        '    {"title": "string", "rationale": "string", "priority": "high|medium|low"}\n'
        "  ],\n"
        '  "contribution_opportunities": ["string"]\n'
        "}\n"
        "Requirements:\n"
        "1. Provide at least 3 distinct recommendations with valid priority.\n"
        "2. Do not enclose the output in markdown codeblocks.\n"
        "3. Do not include any bracketed placeholders.\n"
    )

    return f"{schema_instruction}\nContext:\n{json.dumps(context, indent=2)}"
