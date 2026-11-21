import ast
import os
import sys
from unittest.mock import MagicMock
import pytest


def get_project_files() -> list[str]:
    ignored_dirs = {".git", ".venv", ".venv-verify", ".pytest_cache", "__pycache__"}
    matched: list[str] = []
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in ignored_dirs]
        for file in files:
            matched.append(os.path.join(root, file))
    return matched


def test_no_em_or_en_dashes() -> None:
    em_dash = chr(0x2014)
    en_dash = chr(0x2013)
    violations: list[str] = []
    for path in get_project_files():
        if path.endswith((".png", ".jpg", ".ico", ".pyc")):
            continue
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                if em_dash in content:
                    violations.append(f"{path}: contains em-dash (U+2014)")
                if en_dash in content:
                    violations.append(f"{path}: contains en-dash (U+2013)")
        except Exception as err:
            violations.append(f"{path}: could not read ({err})")

    assert not violations, "Found prohibited dashes:\n" + "\n".join(violations)


def test_requirements_fully_pinned() -> None:
    req_path = "requirements.txt"
    assert os.path.exists(req_path), "requirements.txt does not exist"
    with open(req_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    assert lines, "requirements.txt is empty"
    for line in lines:
        assert "==" in line, f"Requirement not pinned with ==: {line}"
        assert not line.startswith("-e"), f"Editable requirement found: {line}"


def test_env_example_rules() -> None:
    env_example = ".env.example"
    assert os.path.exists(env_example), ".env.example does not exist"
    with open(env_example, "r", encoding="utf-8") as f:
        lines = [line.rstrip("\r\n") for line in f]

    for line in lines:
        assert not line.startswith("#"), f"Comment line in .env.example: {line}"

    var_names = [line.split("=")[0].strip() for line in lines if "=" in line]
    assert var_names, "No variables found in .env.example"

    with open("src/config.py", "r", encoding="utf-8") as f:
        config_content = f.read()

    for var in var_names:
        assert var in config_content, f"Variable {var} from .env.example is not used in src/config.py"


def test_no_api_keys_or_tokens() -> None:
    p1 = "".join(["g", "s", "k", "_"])
    p2 = "".join(["g", "h", "p", "_"])
    forbidden = [p1, p2]
    violations: list[str] = []
    for path in get_project_files():
        if path.endswith((".png", ".jpg", ".ico", ".pyc")):
            continue
        if os.path.basename(path) == "test_project_rules.py":
            continue
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line_no, line in enumerate(f, start=1):
                for token in forbidden:
                    if token in line:
                        violations.append(f"{path}:{line_no} contains prefix {token}")

    assert not violations, "Found sensitive token prefixes:\n" + "\n".join(violations)


def test_config_imports_cleanly_without_env_or_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    sys.modules.pop("src.config", None)
    import src.config
    assert hasattr(src.config, "GROQ_MODEL")
    assert src.config.GROQ_MODEL == "openai/gpt-oss-120b"


def test_st_secrets_not_consulted_when_env_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "env_provided_key")
    mock_st = MagicMock()
    monkeypatch.setitem(sys.modules, "streamlit", mock_st)

    from src.config import get_secret
    res = get_secret("GROQ_API_KEY")
    assert res == "env_provided_key"
    mock_st.secrets.get.assert_not_called()


def test_ast_type_hints_and_line_limits() -> None:
    target_files = ["app.py"]
    for root, _, files in os.walk("src"):
        for file in files:
            if file.endswith(".py"):
                target_files.append(os.path.join(root, file))

    violations: list[str] = []
    for path in target_files:
        with open(path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=path)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                length = (node.end_lineno or 0) - node.lineno + 1
                if length > 50:
                    violations.append(f"{path}:{node.name} exceeds 50 lines ({length} lines)")

                if node.returns is None:
                    violations.append(f"{path}:{node.name} lacks return type annotation")

                for arg in node.args.args:
                    if arg.arg in ("self", "cls"):
                        continue
                    if arg.annotation is None:
                        violations.append(f"{path}:{node.name} arg '{arg.arg}' lacks type annotation")

    assert not violations, "AST check violations:\n" + "\n".join(violations)


def test_no_langchain_or_llama_index_imports() -> None:
    forbidden = ["langchain", "llama_index"]
    target_files = ["app.py"]
    for folder in ("src", "tests"):
        for root, _, files in os.walk(folder):
            for file in files:
                if file.endswith(".py"):
                    target_files.append(os.path.join(root, file))

    violations: list[str] = []
    for path in target_files:
        with open(path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if any(pkg in alias.name for pkg in forbidden):
                        violations.append(f"{path} imports {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module and any(pkg in node.module for pkg in forbidden):
                    violations.append(f"{path} imports from {node.module}")

    assert not violations, "Prohibited framework imports:\n" + "\n".join(violations)
