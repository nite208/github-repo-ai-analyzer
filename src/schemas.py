import re
from typing import Literal
from pydantic import BaseModel, Field, field_validator, model_validator


def _check_no_placeholder(text: str) -> None:
    pattern = r"\[(?:insert|placeholder|todo|your|repo|component|name|x|y).*?\]"
    if re.search(pattern, text, re.IGNORECASE):
        raise ValueError("Field contains bracketed placeholder")


class Recommendation(BaseModel):
    title: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    priority: Literal["high", "medium", "low"]

    @field_validator("title", "rationale")
    @classmethod
    def validate_text(cls, value: str) -> str:
        _check_no_placeholder(value)
        return value.strip()


class RepoAnalysis(BaseModel):
    executive_summary: str = Field(min_length=1)
    tech_stack: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    architecture_and_organization: str = Field(min_length=1)
    recommendations: list[Recommendation] = Field(min_length=3)
    contribution_opportunities: list[str] = Field(default_factory=list)

    @field_validator("executive_summary", "architecture_and_organization")
    @classmethod
    def validate_narratives(cls, value: str) -> str:
        _check_no_placeholder(value)
        return value.strip()

    @field_validator("tech_stack", "strengths", "contribution_opportunities")
    @classmethod
    def validate_lists(cls, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        for item in values:
            _check_no_placeholder(item)
            cleaned.append(item.strip())
        return cleaned

    @model_validator(mode="after")
    def validate_recommendations_count(self) -> "RepoAnalysis":
        if len(self.recommendations) < 3:
            raise ValueError("Analysis must contain at least 3 recommendations")
        return self
