"""Google Gemini-backed, evidence-limited explanations for completed HR audits."""
import json
import logging
import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from pydantic import ValidationError

from backend.schemas.audit_explainer import AuditExplanation


logger = logging.getLogger(__name__)
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")
GEMINI_GENERATE_CONTENT_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)


class AIConfigurationError(Exception):
    """Raised when the optional AI feature has not been configured."""


class AIProviderError(Exception):
    """Raised when the AI provider cannot complete a request."""

    def __init__(self, message: str = "", status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class AIResponseError(Exception):
    """Raised when the AI provider returns unusable or unsupported content."""


def explain_audit(overall_score: float, category_scores: list[dict]) -> AuditExplanation:
    """Generate concise guidance using only aggregate audit score data."""
    api_key = os.getenv("AI_API_KEY", "").strip()
    if not api_key:
        raise AIConfigurationError(
            "The AI explainer is not configured. Add AI_API_KEY to the backend .env file."
        )

    model = os.getenv("AI_MODEL", "gemini-2.5-flash").strip()
    if not model:
        raise AIConfigurationError("AI_MODEL must name a supported Gemini model.")

    score_data = [
        {
            "category": item["category"],
            "score": item["score"],
            "priority": item["priority"],
            "gap_description": item["gap_description"],
        }
        for item in category_scores
    ]
    system_instruction = (
        "You explain HR audit results to a startup. Use only the supplied overall "
        "score and category scores/descriptions. Do not invent facts, company details, "
        "laws, or policies. Give practical, low-risk process improvements, not legal "
        "advice or decisions about individual employees. Return only a JSON object "
        "with a summary and actions array. Each action must have category, priority, "
        "explanation, and next_step. Only include categories supplied in the audit "
        "data, and copy their priority exactly. Include at most one action per category "
        "and no more than six actions. Focus on HIGH and MEDIUM priorities; actions "
        "may be empty when none exist."
    )
    prompt = json.dumps(
        {"overall_score": overall_score, "category_scores": score_data},
        ensure_ascii=True,
    )

    try:
        response = requests.post(
            GEMINI_GENERATE_CONTENT_URL.format(model=model),
            headers={"x-goog-api-key": api_key},
            json={
                "systemInstruction": {"parts": [{"text": system_instruction}]},
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "temperature": 0.2,
                },
            },
            timeout=30,
        )
        response.raise_for_status()
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else None
        logger.warning("Gemini API request failed with HTTP status %s", status_code)
        if status_code in (400, 401, 403):
            raise AIConfigurationError(
                "Google Gemini rejected the API key or request. Check that AI_API_KEY "
                "is a Gemini API key and that the Generative Language API is enabled."
            ) from exc
        raise AIProviderError(status_code=status_code) from exc
    except requests.RequestException as exc:
        logger.warning("Gemini API request failed: %s", exc.__class__.__name__)
        raise AIProviderError from exc

    try:
        parts = response.json()["candidates"][0]["content"]["parts"]
        content = "".join(part["text"] for part in parts if "text" in part)
        parsed = json.loads(content)
        explanation = AuditExplanation.model_validate(parsed)
    except (ValueError, KeyError, IndexError, TypeError, ValidationError) as exc:
        logger.warning("Gemini returned an invalid audit explanation")
        raise AIResponseError from exc

    source_priorities = {item["category"]: item["priority"] for item in score_data}
    action_categories = [action.category for action in explanation.actions]
    if (
        len(action_categories) != len(set(action_categories))
        or any(
            source_priorities.get(action.category) != action.priority
            for action in explanation.actions
        )
    ):
        logger.warning("Gemini returned an explanation inconsistent with audit scores")
        raise AIResponseError

    return explanation
