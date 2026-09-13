"""Pydantic schemas for the Audit API (request/response validation)."""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class QuestionOptionOut(BaseModel):
    id: int
    label: str

    class Config:
        from_attributes = True


class QuestionOut(BaseModel):
    id: int
    text: str
    category_id: int
    category_name: Optional[str] = None
    order: Optional[int] = 0
    options: List[QuestionOptionOut]

    class Config:
        from_attributes = True


class SubmitAnswer(BaseModel):
    question_id: int
    selected_option_id: int


class SubmitAuditRequest(BaseModel):
    startup_id: int
    answers: List[SubmitAnswer]


class CategoryScoreOut(BaseModel):
    category: str
    score: float
    gap_description: Optional[str] = None
    priority: Optional[str] = None


class AuditResultOut(BaseModel):
    audit_id: int
    overall_score: float
    status: str
    category_scores: List[CategoryScoreOut]


class AuditSummaryOut(BaseModel):
    """Lightweight row for an audit history list — no per-category detail."""
    audit_id: int
    status: str
    overall_score: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
