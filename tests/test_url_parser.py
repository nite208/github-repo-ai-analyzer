import pytest
from src.exceptions import InvalidRepoUrlError
from src.url_parser import parse_github_url


@pytest.mark.parametrize(
    "raw_input,expected_owner,expected_repo",
    [
        ("psf/requests", "psf", "requests"),
        ("https://github.com/psf/requests", "psf", "requests"),
        ("http://github.com/psf/requests", "psf", "requests"),
        ("github.com/psf/requests", "psf", "requests"),
        ("https://github.com/psf/requests.git", "psf", "requests"),
        ("https://github.com/psf/requests/", "psf", "requests"),
        ("https://github.com/psf/requests/tree/main", "psf", "requests"),
        ("https://www.github.com/psf/requests/blob/main/README.md", "psf", "requests"),
        ("  psf/requests  ", "psf", "requests"),
        ("pallets/flask.git", "pallets", "flask"),
    ],
)
def test_valid_github_urls(raw_input: str, expected_owner: str, expected_repo: str) -> None:
    owner, repo = parse_github_url(raw_input)
    assert owner == expected_owner
    assert repo == expected_repo


@pytest.mark.parametrize(
    "invalid_input",
    [
        "",
        "   ",
        "singleword",
        "https://gitlab.com/psf/requests",
        "https://github.com/",
        "https://github.com/onlyowner",
        "psf/requests/extra/path",
        "invalid owner/repo",
        "///",
    ],
)
def test_invalid_github_urls(invalid_input: str) -> None:
    with pytest.raises(InvalidRepoUrlError):
        parse_github_url(invalid_input)
