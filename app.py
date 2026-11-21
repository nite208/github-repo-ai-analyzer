from datetime import datetime, timezone
import logging
import streamlit as st
from src.analyzer import analyze_repository
from src.config import CACHE_TTL_SECONDS
from src.exceptions import (
    GitHubNetworkError,
    GitHubNotFoundError,
    GitHubRateLimitError,
    InvalidRepoUrlError,
    LlmAnalysisError,
)
from src.github_client import GitHubClient
from src.llm_client import LLMClient
from src.logging_setup import setup_logging
from src.metrics import RepoMetrics
from src.repo_collector import RepoData, collect_repository_data
from src.schemas import RepoAnalysis
from src.url_parser import parse_github_url

logger = logging.getLogger(__name__)


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def fetch_repo_data(owner: str, repo: str) -> RepoData:
    client = GitHubClient()
    return collect_repository_data(client, owner, repo)


def render_header() -> None:
    st.set_page_config(page_title="GitHub Repo AI Analyzer", layout="wide")
    st.title("GitHub Repository AI Analyzer")
    st.markdown(
        "Enter a public GitHub repository URL or owner/repo to inspect codebase health and AI architecture insights."
    )


def render_metrics_cards(data: RepoData) -> None:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Stars", f"{data.metadata.get('stars', 0):,}")
    col2.metric("Forks", f"{data.metadata.get('forks', 0):,}")
    col3.metric("Open Issues", f"{data.metadata.get('open_issues_count', 0):,}")
    col4.metric("Primary Language", str(data.metadata.get("primary_language", "N/A")))


def render_health_checklist(metrics: RepoMetrics) -> None:
    st.subheader("Repository Health Checklist")
    cols = st.columns(5)
    cols[0].checkbox("README", value=metrics.has_readme, disabled=True)
    cols[1].checkbox("Tests", value=metrics.has_tests, disabled=True)
    cols[2].checkbox("CI Workflow", value=metrics.has_ci, disabled=True)
    cols[3].checkbox("License", value=metrics.has_license, disabled=True)
    cols[4].checkbox("Contributing", value=metrics.has_contributing, disabled=True)

    st.write(
        f"Total files: {metrics.total_files} | README characters: {metrics.readme_length:,} | Top directories: {', '.join(metrics.top_level_directories[:8]) or 'None'}"
    )


def render_languages_chart(percentages: dict[str, float]) -> None:
    if percentages:
        st.subheader("Language Breakdown")
        st.bar_chart(percentages)


def render_analysis_section(analysis: RepoAnalysis) -> None:
    st.subheader("AI Architectural Insights")
    st.markdown("### Executive Summary")
    st.write(analysis.executive_summary)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Tech Stack")
        for item in analysis.tech_stack:
            st.markdown(f"- {item}")
    with col2:
        st.markdown("### Key Strengths")
        for item in analysis.strengths:
            st.markdown(f"- {item}")

    st.markdown("### Architecture and Organization")
    st.write(analysis.architecture_and_organization)

    st.markdown("### Recommendations")
    for rec in analysis.recommendations:
        priority_label = rec.priority.upper()
        st.markdown(f"**[{priority_label}] {rec.title}**")
        st.markdown(f"{rec.rationale}")

    st.markdown("### Contribution Opportunities")
    for opp in analysis.contribution_opportunities:
        st.markdown(f"- {opp}")


def format_reset_time(timestamp: int | None) -> str:
    if not timestamp:
        return "shortly"
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def process_repository(raw_url: str) -> None:
    try:
        owner, repo = parse_github_url(raw_url)
        with st.spinner("Fetching repository data from GitHub REST API..."):
            repo_data = fetch_repo_data(owner, repo)

        render_metrics_cards(repo_data)
        st.divider()
        render_health_checklist(repo_data.metrics)
        render_languages_chart(repo_data.metrics.language_percentages)
        st.divider()

        with st.spinner("Analyzing repository structure with LLM..."):
            llm_client = LLMClient()
            analysis = analyze_repository(repo_data, llm_client)

        render_analysis_section(analysis)

    except InvalidRepoUrlError as err:
        st.error(f"Invalid input: {err}")
    except GitHubNotFoundError:
        st.error("Repository not found or is private. Please verify the URL.")
    except GitHubRateLimitError as err:
        time_str = format_reset_time(err.reset_timestamp)
        st.error(
            f"GitHub API rate limit exceeded. Reset time: {time_str}. "
            "Please provide a GITHUB_TOKEN in settings to increase your rate limits."
        )
    except GitHubNetworkError as err:
        st.error(f"Network error communicating with GitHub: {err}")
    except LlmAnalysisError as err:
        st.error(f"AI Analysis error: {err}")
    except Exception as err:
        logger.error("Unexpected error during processing: %s", err, exc_info=True)
        st.error(f"An unexpected error occurred: {err}")


def main() -> None:
    setup_logging()
    render_header()
    repo_input = st.text_input(
        "Repository URL or owner/repo",
        placeholder="e.g. psf/requests or https://github.com/psf/requests",
    )
    if st.button("Analyze", type="primary"):
        if not repo_input.strip():
            st.warning("Please enter a repository identifier.")
        else:
            process_repository(repo_input)


if __name__ == "__main__":
    main()
