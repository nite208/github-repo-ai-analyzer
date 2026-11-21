# GitHub Repository AI Analyzer

## Overview

GitHub Repository AI Analyzer is a Streamlit web application that inspects public GitHub repositories using the GitHub REST API and produces structured code health assessments along with AI-generated architectural insights via Groq LLMs. The application computes deterministic codebase metrics in code and requests structured analysis from the LLM, validating responses against strict Pydantic schemas.

## Architecture

The project adheres to a modular design where each module has a single responsibility and the UI layer contains no business logic:

- `src/config.py`: Centralized configuration loading environment variables first with graceful fallback to Streamlit secrets and defaults.
- `src/logging_setup.py`: Standard logging configuration across all modules.
- `src/exceptions.py`: Domain-specific exception hierarchy for URL parsing, GitHub API, rate limiting, network errors, and LLM analysis.
- `src/url_parser.py`: Normalizes and validates input URLs or owner/repo strings.
- `src/github_client.py`: Handles HTTP communication with the GitHub REST API with rate limit detection, bearer authentication, and error mapping.
- `src/repo_collector.py`: Coordinates fetching metadata, language statistics, README, file tree, package descriptors, and good-first-issues.
- `src/metrics.py`: Computes deterministic health metrics including test presence, CI workflows, licensing, contributing guidelines, and language percentages.
- `src/schemas.py`: Pydantic models for structured analysis output and validation rules.
- `src/prompt_builder.py`: Builds prompts with character budget truncation for README and file trees.
- `src/llm_client.py`: Interfaces with the Groq SDK for model completions.
- `src/analyzer.py`: Orchestrates prompt construction, LLM invocation, schema validation, and single-attempt retry logic.
- `app.py`: Streamlit user interface rendering input forms, metric cards, language charts, health checklists, and structured AI insights.

## Setup and Run Steps for Git Bash on Windows

1. Create a Python virtual environment:
```bash
python -m venv .venv
```

2. Activate the virtual environment:
```bash
source .venv/Scripts/activate
```

3. Install pinned dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
```
Edit `.env` to set your `GROQ_API_KEY` and optional `GITHUB_TOKEN`.

5. Run the Streamlit application:
```bash
streamlit run app.py
```

6. Run the automated tests:
```bash
python -m pytest -q
```

## Streamlit Cloud Deployment Steps

1. Push this repository to GitHub.
2. Log in to Streamlit Community Cloud and click New App.
3. Select your repository, branch, and set the main file path to `app.py`.
4. In Advanced Settings under Secrets, paste the following configuration:
```toml
GROQ_API_KEY = "your-groq-api-key-here"
GITHUB_TOKEN = "your-github-token-here"
GROQ_MODEL = "openai/gpt-oss-120b"
```
5. Click Deploy.

## Rate Limit Notes

- Unauthenticated GitHub API requests are limited to 60 requests per hour per IP address.
- Providing a personal access token via `GITHUB_TOKEN` increases this limit to 5,000 requests per hour.
- When a rate limit is encountered (HTTP 403 with `X-RateLimit-Remaining: 0` or HTTP 429), the application captures the `X-RateLimit-Reset` timestamp and displays the exact UTC reset time in the user interface.

## Design Decisions

- Deterministic metrics such as file counts, top directories, and CI or test detection are computed purely in Python to avoid hallucinations.
- The LLM receives pre-calculated metrics and truncated context to fit within prompt token budgets while retaining relevant details.
- Schema validation enforces at least three actionable recommendations with priorities and rejects malformed outputs or placeholder strings. A single retry is executed with the validation error message if the first attempt fails.
- Secrets handling queries `os.environ` before attempting `st.secrets`, preventing runtime errors when deployed or run in headless test environments.

## Known Limitations

- Repositories larger than 100,000 tree objects will have truncated file listings due to GitHub recursive tree API limits.
- The default Groq model requires an active API key with available quota.
- Only public repositories or repositories accessible to the configured personal access token can be analyzed.

## Example Repositories to Try

- `psf/requests`
- `pallets/flask`
- `encode/httpx`
- `tiangolo/fastapi`

## Open-Source Contribution

- Target repository: target repository
- Contribution link: contribution link
- Summary: summary
