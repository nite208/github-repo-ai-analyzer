import json
import logging
from pydantic import ValidationError
from src.config import FILE_TREE_CHAR_BUDGET, README_CHAR_BUDGET
from src.exceptions import LlmAnalysisError
from src.llm_client import LLMClient
from src.prompt_builder import build_analysis_prompt, build_system_prompt
from src.repo_collector import RepoData
from src.schemas import RepoAnalysis

logger = logging.getLogger(__name__)


def parse_and_validate_response(raw_text: str) -> RepoAnalysis:
    cleaned = raw_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as err:
        raise ValueError(f"Malformed JSON from LLM: {err}") from err

    return RepoAnalysis.model_validate(data)


def analyze_repository(
    repo_data: RepoData,
    llm_client: LLMClient,
    readme_budget: int = README_CHAR_BUDGET,
    file_tree_budget: int = FILE_TREE_CHAR_BUDGET,
) -> RepoAnalysis:
    system_prompt = build_system_prompt()
    user_prompt = build_analysis_prompt(
        metadata=repo_data.metadata,
        languages=repo_data.languages,
        readme_content=repo_data.readme,
        tree_paths=repo_data.tree_paths,
        package_descriptors=repo_data.package_descriptors,
        good_first_issues=repo_data.good_first_issues,
        readme_budget=readme_budget,
        file_tree_budget=file_tree_budget,
    )

    logger.info("Attempting primary LLM analysis")
    raw_response = llm_client.generate_completion(system_prompt, user_prompt)

    try:
        return parse_and_validate_response(raw_response)
    except (ValidationError, ValueError) as first_err:
        logger.warning("First LLM analysis failed validation: %s. Retrying once.", first_err)
        retry_prompt = (
            f"{user_prompt}\n\n"
            f"Your previous attempt was rejected with error:\n{first_err}\n"
            "Please fix the schema or content errors and output strictly valid JSON."
        )
        try:
            raw_retry = llm_client.generate_completion(system_prompt, retry_prompt)
            return parse_and_validate_response(raw_retry)
        except Exception as retry_err:
            logger.error("LLM retry failed validation: %s", retry_err)
            raise LlmAnalysisError(
                f"Failed to generate structured repository insights after retry: {retry_err}"
            ) from retry_err
