"""
MODULE 6 — HR Gap Detection

Rule-based logic that converts a low category score into an explained
HR gap with a priority level. Thresholds and wording here are PLACEHOLDERS
-- the BBA-HR team should own and refine these rules.
"""

# Threshold below which a category is flagged as a gap
GAP_THRESHOLD = 60.0

GAP_MESSAGES = {
    "Attendance": "Attendance is tracked manually or via spreadsheets, "
                  "creating high administrative effort and limited reporting.",
    "Recruitment": "Recruitment relies on manual or ad-hoc processes, "
                   "slowing hiring and reducing candidate visibility.",
    "Payroll": "Payroll processes are not fully digitized, increasing "
               "the risk of compliance and calculation errors.",
    "Performance Management": "Performance reviews happen infrequently, "
                               "limiting feedback and growth planning.",
    "Employee Engagement": "There is limited structured measurement of "
                            "employee engagement or satisfaction.",
    "HR Analytics": "There is no centralized HR data analysis, making it "
                     "hard to spot trends or make data-driven HR decisions.",
}


def priority_for_score(score: float) -> str:
    if score < 40:
        return "HIGH"
    if score < 60:
        return "MEDIUM"
    return "LOW"


def detect_gaps(category_scores: dict) -> dict:
    """
    Given {category_name: score}, returns {category_name: {gap, priority}}
    for every category under the gap threshold.
    """
    gaps = {}
    for category, score in category_scores.items():
        if score < GAP_THRESHOLD:
            gaps[category] = {
                "gap_description": GAP_MESSAGES.get(
                    category, f"{category} shows room for improvement."
                ),
                "priority": priority_for_score(score),
            }
    return gaps
