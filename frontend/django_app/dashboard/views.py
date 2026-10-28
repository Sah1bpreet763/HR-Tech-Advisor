import requests
from collections import OrderedDict
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from .decorators import session_login_required


CATEGORY_META = {
    "Recruitment": {
        "icon": "bi-people",
        "description": "Candidate pipeline, interview structures, onboarding, and ATS tracking.",
    },
    "Payroll": {
        "icon": "bi-cash-coin",
        "description": "Salary calculations, statutory compliance (PF, ESI, TDS), and expense approvals.",
    },
    "Attendance": {
        "icon": "bi-clock-history",
        "description": "Clock-in tracking, leave policies, anomaly detection, and remote attendance.",
    },
    "Performance Management": {
        "icon": "bi-graph-up-arrow",
        "description": "Goal setting, review frequency, 360 feedback, and performance improvement plans.",
    },
    "Employee Engagement": {
        "icon": "bi-heart-pulse",
        "description": "Satisfaction pulse surveys, attrition control, recognition, and grievance channels.",
    },
    "HR Analytics": {
        "icon": "bi-pie-chart",
        "description": "HR metrics centralization, cost-per-hire, reporting, and data security.",
    },
}


def landing_view(request):
    """
    Public Landing Page styled in the exact Neo-Brutalist desktop aesthetic.
    If already authenticated, redirects directly to the founder dashboard.
    """
    if request.session.get("user_id"):
        return redirect("dashboard:home")
    return render(request, "dashboard/landing.html")


@session_login_required
def home_view(request):
    startup_id = request.session["startup_id"]
    startup = None
    audit_history = []
    latest_result = None

    try:
        s_resp = requests.get(f"{settings.FASTAPI_BASE_URL}/api/startups/{startup_id}", timeout=5)
        if s_resp.status_code == 200:
            startup = s_resp.json()
    except requests.RequestException:
        messages.error(request, "Could not reach backend to load startup profile.")

    try:
        h_resp = requests.get(f"{settings.FASTAPI_BASE_URL}/api/audit/history/{startup_id}", timeout=5)
        if h_resp.status_code == 200:
            audit_history = h_resp.json()
            if audit_history:
                latest_id = audit_history[0]["audit_id"]
                r_resp = requests.get(f"{settings.FASTAPI_BASE_URL}/api/audit/{latest_id}", timeout=5)
                if r_resp.status_code == 200:
                    latest_result = r_resp.json()
    except requests.RequestException:
        pass

    return render(request, "dashboard/home.html", {
        "startup": startup,
        "audit_history": audit_history,
        "latest_result": latest_result,
    })


@session_login_required
def questionnaire_view(request):
    """
    Module 3 — Interactive HR Audit Questionnaire.
    Loads questions from backend grouped by the 6 core HR domains.
    """
    startup_id = request.session["startup_id"]

    try:
        q_resp = requests.get(f"{settings.FASTAPI_BASE_URL}/api/audit/questions", timeout=5)
        if q_resp.status_code != 200:
            messages.error(request, "Failed to load audit questions from backend.")
            return redirect("dashboard:home")
        questions = q_resp.json()
    except requests.RequestException:
        messages.error(request, "Could not reach the HR-Tech Advisor backend.")
        return redirect("dashboard:home")

    # Group questions by category
    categories = OrderedDict()
    for q in questions:
        cname = q.get("category_name") or "General"
        if cname not in categories:
            categories[cname] = {
                "name": cname,
                "icon": CATEGORY_META.get(cname, {}).get("icon", "bi-check2-circle"),
                "description": CATEGORY_META.get(cname, {}).get("description", ""),
                "questions": [],
            }
        categories[cname]["questions"].append(q)

    if request.method == "POST":
        answers = []
        missing_questions = []

        for q in questions:
            qid = q["id"]
            selected = request.POST.get(f"question_{qid}")
            if selected:
                answers.append({"question_id": int(qid), "selected_option_id": int(selected)})
            else:
                missing_questions.append(qid)

        if missing_questions:
            messages.error(
                request,
                f"Please answer all {len(questions)} questions before submitting. ({len(missing_questions)} remaining)"
            )
            # Re-render with existing answers preserved in context
            current_answers = {
                int(q["id"]): int(request.POST.get(f"question_{q['id']}"))
                for q in questions if request.POST.get(f"question_{q['id']}")
            }
            return render(request, "dashboard/questionnaire.html", {
                "categories": list(categories.values()),
                "total_questions": len(questions),
                "selected_answers": current_answers,
            })

        # Submit to backend scoring engine
        try:
            sub_resp = requests.post(
                f"{settings.FASTAPI_BASE_URL}/api/audit/submit",
                json={"startup_id": startup_id, "answers": answers},
                timeout=10,
            )
            if sub_resp.status_code == 200:
                result = sub_resp.json()
                messages.success(request, "HR Audit submitted successfully! Check your diagnostic score and recommendations below.")
                return redirect("dashboard:audit_results", audit_id=result["audit_id"])
            else:
                detail = sub_resp.json().get("detail", "Error submitting audit.")
                messages.error(request, f"Submission error: {detail}")
        except requests.RequestException:
            messages.error(request, "Connection failed while submitting audit answers.")

    return render(request, "dashboard/questionnaire.html", {
        "categories": list(categories.values()),
        "total_questions": len(questions),
        "selected_answers": {},
    })


@session_login_required
def audit_results_view(request, audit_id):
    """
    Displays the comprehensive HR Health Report: Score gauge, Domain breakdown,
    Identified gaps, Tool recommendations, and the 3-Month Implementation Roadmap.
    """
    startup_id = request.session["startup_id"]
    ai_explanation = None
    try:
        res_resp = requests.get(f"{settings.FASTAPI_BASE_URL}/api/audit/{audit_id}", timeout=5)
        if res_resp.status_code == 404:
            raise Http404("Audit not found.")
        if res_resp.status_code != 200:
            messages.error(request, "Could not load audit results.")
            return redirect("dashboard:home")
        audit_result = res_resp.json()

        # Fetch recommendations
        rec_resp = requests.get(f"{settings.FASTAPI_BASE_URL}/api/recommendations/{audit_id}", timeout=5)
        recommendations = rec_resp.json() if rec_resp.status_code == 200 else []

        # Fetch startup
        s_resp = requests.get(f"{settings.FASTAPI_BASE_URL}/api/startups/{startup_id}", timeout=5)
        startup = s_resp.json() if s_resp.status_code == 200 else {}
    except requests.RequestException:
        messages.error(request, "Could not reach backend to load audit details.")
        return redirect("dashboard:home")

    if request.method == "POST" and request.POST.get("action") == "explain_audit":
        try:
            explanation_resp = requests.post(
                f"{settings.FASTAPI_BASE_URL}/api/audit/{audit_id}/explanation",
                params={"startup_id": startup_id},
                timeout=35,
            )
            if explanation_resp.status_code == 200:
                ai_explanation = explanation_resp.json()
            else:
                try:
                    detail = explanation_resp.json().get(
                        "detail", "The AI explanation could not be generated."
                    )
                except ValueError:
                    detail = "The AI explanation could not be generated."
                messages.error(request, detail)
        except requests.RequestException:
            messages.error(request, "Could not reach the AI explanation service.")

    # Build 3-Month Roadmap based on gap priorities
    high_gaps = [cs for cs in audit_result["category_scores"] if cs.get("priority") == "HIGH"]
    med_gaps = [cs for cs in audit_result["category_scores"] if cs.get("priority") == "MEDIUM"]

    m1_focus = high_gaps[0]["category"] if high_gaps else (med_gaps[0]["category"] if med_gaps else "Payroll & Compliance Verification")
    m2_focus = (high_gaps[1]["category"] if len(high_gaps) > 1 else (med_gaps[0]["category"] if (high_gaps and med_gaps) else (med_gaps[1]["category"] if len(med_gaps) > 1 else "Performance Management")))
    m3_focus = "HR Analytics & Metrics" if "HR Analytics" not in (m1_focus, m2_focus) else "Culture & Continuous Engagement"

    roadmap = [
        {
            "month": "Month 1",
            "tag": "Critical & Immediate",
            "color": "danger",
            "focus": f"{m1_focus} Automation",
            "description": "Stop manual spreadsheets immediately. Implement automated workflow software to cut operational friction and mitigate compliance liabilities.",
            "actions": [
                f"Procure and configure tooling for {m1_focus}",
                "Migrate legacy records and configure access permissions",
                "Conduct team onboarding and establish standardized procedures",
            ],
        },
        {
            "month": "Month 2",
            "tag": "Process Stabilization",
            "color": "warning",
            "focus": f"{m2_focus} Systematization",
            "description": "Establish transparent, recurring review structures and standardize employee communication to maintain operational cadence.",
            "actions": [
                f"Roll out structured policies for {m2_focus}",
                "Train team leads and managers on scorecards and rubrics",
                "Integrate review milestones into monthly planning rituals",
            ],
        },
        {
            "month": "Month 3",
            "tag": "Scale & Optimization",
            "color": "success",
            "focus": f"{m3_focus} Insights",
            "description": "Activate centralized analytics dashboards to monitor talent flight-risk, hiring costs, and team happiness in real-time.",
            "actions": [
                f"Set up reporting dashboards for {m3_focus}",
                "Establish quarterly leadership review of talent health metrics",
                "Benchmark team compensation and retention against peer startups",
            ],
        },
    ]

    return render(request, "dashboard/audit_results.html", {
        "audit_result": audit_result,
        "recommendations": recommendations,
        "roadmap": roadmap,
        "startup": startup,
        "audit_id": audit_id,
        "ai_explanation": ai_explanation,
    })


@session_login_required
def audit_history_view(request):
    startup_id = request.session["startup_id"]
    history = []
    try:
        resp = requests.get(f"{settings.FASTAPI_BASE_URL}/api/audit/history/{startup_id}", timeout=5)
        if resp.status_code == 200:
            history = resp.json()
    except requests.RequestException:
        messages.error(request, "Could not load audit history.")

    return render(request, "dashboard/audit_history.html", {"history": history})


@session_login_required
def audit_pdf_download_view(request, audit_id):
    """
    Downloads executive PDF report from FastAPI backend.
    """
    try:
        resp = requests.get(f"{settings.FASTAPI_BASE_URL}/api/reports/{audit_id}/pdf", timeout=10)
        if resp.status_code == 200:
            response = HttpResponse(resp.content, content_type="application/pdf")
            response["Content-Disposition"] = resp.headers.get(
                "Content-Disposition", f'attachment; filename="HR_Health_Report_{audit_id}.pdf"'
            )
            return response
        else:
            messages.error(request, "PDF report generation failed or audit is not completed.")
            return redirect("dashboard:audit_results", audit_id=audit_id)
    except requests.RequestException:
        messages.error(request, "Failed to connect to report generation service.")
        return redirect("dashboard:audit_results", audit_id=audit_id)
