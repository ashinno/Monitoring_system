from __future__ import annotations

from pydantic import BaseModel, Field, ValidationError, field_validator
from typing import Literal


RiskLevel = Literal["BENIGN", "SUSPICIOUS", "MALICIOUS"]


class LLMAssessment(BaseModel):
    risk_level: RiskLevel
    threat_type: str = Field(min_length=1, max_length=120)
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = Field(min_length=1, max_length=1500)
    recommended_actions: list[str] = Field(default_factory=list)

    @field_validator("recommended_actions")
    @classmethod
    def normalize_actions(cls, value: list[str]) -> list[str]:
        allowed = {
            "isolate_host",
            "block_ip",
            "reset_password",
            "investigate_process_tree",
            "collect_forensics",
        }
        normalized = []
        for action in value:
            text = str(action).strip().lower().replace(" ", "_")
            if text in allowed:
                normalized.append(text)
        return normalized


def validate_assessment(payload: dict) -> tuple[LLMAssessment | None, str | None]:
    try:
        parsed = LLMAssessment.model_validate(payload)
        return parsed, None
    except ValidationError as exc:
        return None, str(exc)

