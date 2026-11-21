import logging
import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

logger = logging.getLogger(__name__)


def get_secret(key: str, default: str | None = None) -> str | None:
    if key in os.environ:
        val = os.environ[key]
        if val != "":
            return val
        return default
    try:
        import streamlit as st

        secrets_obj = getattr(st, "secrets", None)
        if secrets_obj is not None:
            found = secrets_obj.get(key)
            if found is not None and str(found) != "":
                return str(found)
    except Exception:
        return default
    return default


GROQ_API_KEY: str | None = get_secret("GROQ_API_KEY")
GITHUB_TOKEN: str | None = get_secret("GITHUB_TOKEN")
GROQ_MODEL: str = (
    get_secret("GROQ_MODEL", "openai/gpt-oss-120b") or "openai/gpt-oss-120b"
)
CACHE_TTL_SECONDS: int = int(get_secret("CACHE_TTL_SECONDS", "300") or 300)
README_CHAR_BUDGET: int = int(get_secret("README_CHAR_BUDGET", "8000") or 8000)
FILE_TREE_CHAR_BUDGET: int = int(
    get_secret("FILE_TREE_CHAR_BUDGET", "4000") or 4000
)
USER_AGENT: str = (
    get_secret(
        "USER_AGENT",
        "GhanexAssessmentAgent/1.0 (https://github.com/nite208/github-repo-ai-analyzer; niteshkumawat2331@gmail.com)",
    )
    or "GhanexAssessmentAgent/1.0 (https://github.com/nite208/github-repo-ai-analyzer; niteshkumawat2331@gmail.com)"
)
