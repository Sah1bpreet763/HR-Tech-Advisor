"""
MODULE 8 — Recommendation Engine (Version 1: Rule-Based)

Compares a startup's profile + HR gaps against the HRTool database and
computes an explainable "Tool Fit Score" for each tool, per the plan:

    Feature Match + Budget Fit + Team Size Fit + Growth Fit + Gap Match
    -> Overall Fit

This is intentionally rule-based (no ML) so it's valid for an MVP.
ML (Module 8, Version 2) can later replace/augment `fit_score()`.
"""
from sqlalchemy.orm import Session
from database import models


def team_size_fit(tool: models.HRTool, team_size: int) -> float:
    if tool.min_team_size <= team_size <= tool.max_team_size:
        return 100.0
    # partial credit if just outside the range
    distance = min(abs(team_size - tool.min_team_size), abs(team_size - tool.max_team_size))
    return max(0.0, 100.0 - distance * 2)


def budget_fit(tool: models.HRTool, monthly_budget: float) -> float:
    if monthly_budget is None or monthly_budget <= 0:
        return 50.0  # unknown budget -> neutral score
    if tool.monthly_cost <= monthly_budget:
        return 100.0
    overage_ratio = (tool.monthly_cost - monthly_budget) / monthly_budget
    return max(0.0, 100.0 - overage_ratio * 100)


def gap_match(tool: models.HRTool, gap_category_ids: set) -> float:
    return 100.0 if tool.category_id in gap_category_ids else 40.0


def fit_score(tool: models.HRTool, startup: models.Startup, gap_category_ids: set) -> dict:
    scores = {
        "team_size_fit": round(team_size_fit(tool, startup.team_size or 0), 1),
        "budget_fit": round(budget_fit(tool, startup.hr_budget_monthly), 1),
        "gap_match": round(gap_match(tool, gap_category_ids), 1),
    }
    overall = round(sum(scores.values()) / len(scores), 1)
    scores["overall_fit"] = overall
    return scores


def build_reason(tool: models.HRTool, scores: dict, startup: models.Startup) -> str:
    reasons = []
    if scores["gap_match"] >= 80:
        reasons.append("addresses one of your identified HR gaps")
    if scores["budget_fit"] >= 80:
        reasons.append("fits within your HR budget")
    if scores["team_size_fit"] >= 80:
        reasons.append(f"suits your team size of {startup.team_size}")
    if not reasons:
        reasons.append("is a reasonable general-purpose option for your profile")
    return f"Recommended because it {', '.join(reasons)}."


def recommend_tools(db: Session, startup: models.Startup, gap_categories: list, top_n: int = 3):
    """
    Returns the top_n ranked HR tools with fit scores and explanations.
    `gap_categories` is a list of category names flagged as gaps.
    """
    gap_category_ids = {
        c.id for c in db.query(models.Category).filter(models.Category.name.in_(gap_categories))
    }

    results = []
    for tool in db.query(models.HRTool).all():
        scores = fit_score(tool, startup, gap_category_ids)
        results.append({
            "tool": tool,
            "scores": scores,
            "reason": build_reason(tool, scores, startup),
        })

    results.sort(key=lambda r: r["scores"]["overall_fit"], reverse=True)
    return results[:top_n]
