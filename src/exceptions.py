class RepoAnalyzerError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvalidRepoUrlError(RepoAnalyzerError):
    pass


class GitHubApiError(RepoAnalyzerError):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class GitHubNotFoundError(GitHubApiError):
    pass


class GitHubRateLimitError(GitHubApiError):
    def __init__(self, message: str, reset_timestamp: int | None = None) -> None:
        super().__init__(message, status_code=429)
        self.reset_timestamp = reset_timestamp


class GitHubNetworkError(GitHubApiError):
    pass


class LlmAnalysisError(RepoAnalyzerError):
    pass
