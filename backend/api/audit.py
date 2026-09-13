"""
MODULE 5/6 API — Questionnaire, submit answers, get scored + gapped result,
and retrieve past audits (Phase 4 completion: submit was write-only before —
there was no way to look back at a completed audit or list a startup's history).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from database.database import get_db
from database import models
from backend.schemas.audit import (
    SubmitAuditRequest, AuditResultOut, CategoryScoreOut, QuestionOut, AuditSummaryOut,
)
from backend.services.scoring_engine import score_audit, score_label
from backend.services.audit_engine import detect_gaps

router = APIRouter()


@router.get("/questions", response_model=list[QuestionOut])
def get_questions(db: Session = Depends(get_db)):
    """Returns the active HR questionnaire, loaded from the database."""
    return (
        db.query(models.Question)
        .filter(models.Question.is_active == True)
        .order_by(models.Question.category_id, models.Question.order)
        .all()
    )


@router.post("/submit", response_model=AuditResultOut)
def submit_audit(payload: SubmitAuditRequest, db: Session = Depends(get_db)):
    startup = db.query(models.Startup).get(payload.startup_id)
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")

    if not payload.answers:
        raise HTTPException(status_code=400, detail="At least one answer is required")

    # Data-integrity check: every selected_option_id must actually belong to
    # its claimed question_id. Without this, a malformed or malicious payload
    # (e.g. answers from a different question set) would silently corrupt
    # scoring — the scoring engine would average in an option's score_value
    # under the wrong question/category with no error raised anywhere.
    question_ids = [a.question_id for a in payload.answers]
    questions = db.query(models.Question).filter(models.Question.id.in_(question_ids)).all()
    questions_by_id = {q.id: q for q in questions}

    for ans in payload.answers:
        question = questions_by_id.get(ans.question_id)
        if not question:
            raise HTTPException(status_code=400, detail=f"Question {ans.question_id} does not exist")
        valid_option_ids = {opt.id for opt in question.options}
        if ans.selected_option_id not in valid_option_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Option {ans.selected_option_id} is not a valid choice for question {ans.question_id}",
            )

    audit = models.Audit(startup_id=startup.id, status="in_progress")
    db.add(audit)
    db.flush()

    for ans in payload.answers:
        db.add(models.Response(
            audit_id=audit.id,
            question_id=ans.question_id,
            selected_option_id=ans.selected_option_id,
        ))
    db.flush()
    db.refresh(audit)

    result = score_audit(db, audit)
    gaps = detect_gaps(result["category_scores"])

    category_score_rows = []
    for category_name, score in result["category_scores"].items():
        gap_info = gaps.get(category_name, {})
        category = db.query(models.Category).filter(models.Category.name == category_name).first()
        db.add(models.CategoryScore(
            audit_id=audit.id,
            category_id=category.id,
            score=score,
            gap_description=gap_info.get("gap_description"),
            priority=gap_info.get("priority"),
        ))
        category_score_rows.append(CategoryScoreOut(
            category=category_name,
            score=score,
            gap_description=gap_info.get("gap_description"),
            priority=gap_info.get("priority"),
        ))

    audit.overall_score = result["overall_score"]
    audit.status = "completed"
    audit.completed_at = datetime.utcnow()
    db.commit()

    return AuditResultOut(
        audit_id=audit.id,
        overall_score=result["overall_score"],
        status=score_label(result["overall_score"]),
        category_scores=category_score_rows,
    )


@router.get("/history/{startup_id}", response_model=list[AuditSummaryOut])
def get_audit_history(startup_id: int, db: Session = Depends(get_db)):
    """Every past audit for a startup, most recent first."""
    startup = db.query(models.Startup).get(startup_id)
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")

    return [
        AuditSummaryOut(
            audit_id=a.id,
            status=a.status,
            overall_score=a.overall_score,
            created_at=a.created_at,
            completed_at=a.completed_at,
        )
        for a in startup.audits  # already ordered newest-first, see models.py
    ]


@router.get("/{audit_id}", response_model=AuditResultOut)
def get_audit(audit_id: int, db: Session = Depends(get_db)):
    """Retrieve a previously completed audit's full scored result."""
    audit = db.query(models.Audit).get(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    if audit.status != "completed":
        raise HTTPException(status_code=409, detail="This audit is not yet completed")

    category_score_rows = [
        CategoryScoreOut(
            category=cs.category.name,
            score=cs.score,
            gap_description=cs.gap_description,
            priority=cs.priority,
        )
        for cs in audit.scores
    ]

    return AuditResultOut(
        audit_id=audit.id,
        overall_score=audit.overall_score,
        status=score_label(audit.overall_score),
        category_scores=category_score_rows,
    )
