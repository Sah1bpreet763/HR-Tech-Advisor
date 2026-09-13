"""MODULE 8 API — Ranked tool recommendations for a completed audit."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.database import get_db
from database import models
from backend.services.recommendation_engine import recommend_tools

router = APIRouter()


@router.get("/{audit_id}")
def get_recommendations(audit_id: int, db: Session = Depends(get_db)):
    audit = db.query(models.Audit).get(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    gap_categories = [cs.category.name for cs in audit.scores if cs.priority in ("HIGH", "MEDIUM")]
    ranked = recommend_tools(db, audit.startup, gap_categories)

    # Persist the recommendations against this audit (Phase 3 completeness:
    # the `recommendations` table should actually hold data, not just exist).
    # Re-running recommendations for the same audit replaces the old rows
    # rather than piling up duplicates/stale entries.
    db.query(models.Recommendation).filter(models.Recommendation.audit_id == audit_id).delete()
    for r in ranked:
        db.add(models.Recommendation(
            audit_id=audit_id,
            tool_id=r["tool"].id,
            fit_score=r["scores"]["overall_fit"],
            reason=r["reason"],
        ))
    db.commit()

    return [
        {
            "tool_name": r["tool"].name,
            "overall_fit": r["scores"]["overall_fit"],
            "breakdown": r["scores"],
            "reason": r["reason"],
        }
        for r in ranked
    ]
