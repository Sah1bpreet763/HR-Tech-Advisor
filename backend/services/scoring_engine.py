"""
MODULE 5 — HR Audit & Scoring Engine

Turns a startup's raw answers into per-category scores and a weighted
overall HR Health Score, exactly as described in the project plan.
"""
from sqlalchemy.orm import Session
from database import models


def score_audit(db: Session, audit: models.Audit) -> dict:
    """
    Computes category scores + overall weighted score for an audit,
    based on the AnswerOptions the startup selected.

    Returns:
        {
          "category_scores": {category_name: score_0_100, ...},
          "overall_score": float
        }
    """
    category_totals = {}   # category_id -> [scores]
    categories = {c.id: c for c in db.query(models.Category).all()}

    for response in audit.responses:
        option = db.query(models.AnswerOption).get(response.selected_option_id)
        question = db.query(models.Question).get(response.question_id)
        category_totals.setdefault(question.category_id, []).append(option.score_value)

    category_scores = {}
    weighted_sum = 0.0
    weight_total = 0.0

    for cat_id, scores in category_totals.items():
        category = categories[cat_id]
        avg_score = sum(scores) / len(scores)
        category_scores[category.name] = round(avg_score, 1)

        weighted_sum += avg_score * category.weight
        weight_total += category.weight

    overall_score = round(weighted_sum / weight_total, 1) if weight_total else 0.0

    return {
        "category_scores": category_scores,
        "overall_score": overall_score,
    }


def score_label(overall_score: float) -> str:
    """Maps a numeric score to the status label shown on the dashboard."""
    if overall_score >= 80:
        return "EXCELLENT"
    if overall_score >= 60:
        return "GOOD"
    if overall_score >= 40:
        return "NEEDS IMPROVEMENT"
    return "CRITICAL"
