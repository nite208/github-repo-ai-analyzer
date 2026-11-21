import logging
from groq import Groq
from src.config import GROQ_API_KEY, GROQ_MODEL
from src.exceptions import LlmAnalysisError

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(
        self,
        api_key: str | None = GROQ_API_KEY,
        model: str = GROQ_MODEL,
        timeout: float = 60.0,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def generate_completion(self, system_prompt: str, user_prompt: str) -> str:
        if not self.api_key:
            raise LlmAnalysisError(
                "GROQ_API_KEY is not configured. Please provide an API key."
            )
        logger.info("Calling Groq LLM model: %s", self.model)
        try:
            client = Groq(api_key=self.api_key, timeout=self.timeout)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            choice = response.choices[0]
            content = choice.message.content
            if not content:
                raise LlmAnalysisError("LLM returned an empty response.")
            return content.strip()
        except LlmAnalysisError:
            raise
        except Exception as err:
            logger.error("Groq API invocation failed: %s", err, exc_info=True)
            raise LlmAnalysisError(f"LLM API failure: {err}") from err
