"""API endpoint for AI explanations of completed HR audits."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.schemas.audit_explainer import AuditExplanation
from backend.services.ai_advisor import (
    AIConfigurationError,
    AIProviderError,
    AIResponseError,
    explain_audit,
)
from backend.services.audit_engine import priority_for_score
from database import models
from database.database import get_db


router = APIRouter()


@router.post("/{audit_id}/explanation", response_model=AuditExplanation)
def post_audit_explanation(
    audit_id: int,
    startup_id: int = Query(...),
    db: Session = Depends(get_db),
):
    audit = db.query(models.Audit).filter(models.Audit.id == audit_id).first()
    if not audit or audit.startup_id != startup_id:
        raise HTTPException(status_code=404, detail="Audit not found")
    if audit.status != "completed":
        raise HTTPException(status_code=409, detail="This audit is not yet completed")
    if audit.overall_score is None:
        raise HTTPException(status_code=409, detail="This audit has no scored results")

    category_scores = [
        {
            "category": score.category.name,
            "score": score.score,
            "priority": score.priority or priority_for_score(score.score),
            "gap_description": score.gap_description or "",
        }
        for score in audit.scores
    ]

    try:
        return explain_audit(audit.overall_score, category_scores)
    except AIConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except AIProviderError as exc:
        if exc.status_code == 429:
            raise HTTPException(
                status_code=503,
                detail="Google Gemini API quota or rate limit reached. Check the API quota and try again.",
            ) from exc
        raise HTTPException(
            status_code=503,
            detail="Google Gemini is temporarily unavailable. Please try again.",
        ) from exc
    except AIResponseError as exc:
        raise HTTPException(
            status_code=502,
            detail="The AI service returned an invalid explanation. Please try again.",
        ) from exc
