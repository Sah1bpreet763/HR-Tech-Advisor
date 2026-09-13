"""
Comprehensive integration and unit test suite for HR-Tech Advisor.
Tests Modules 1, 2, 3, 5, 6, 8, and 10 end-to-end.
"""
import pytest
from fastapi.testclient import TestClient
from database.database import SessionLocal, Base, engine
from database import models
from backend.main import app
from backend.services.scoring_engine import score_label
from backend.services.report_generator import generate_audit_pdf

client = TestClient(app)


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    yield session
    session.close()


def test_module_1_framework_integrity(db):
    """Confirm 6 categories and 30 questions are populated and configured."""
    categories = db.query(models.Category).all()
    assert len(categories) == 6
    category_names = {c.name for c in categories}
    expected_categories = {
        "Recruitment", "Payroll", "Attendance",
        "Performance Management", "Employee Engagement", "HR Analytics"
    }
    assert category_names == expected_categories

    questions = db.query(models.Question).all()
    assert len(questions) == 30
    for q in questions:
        assert len(q.options) >= 4
        assert q.category_name != ""


def test_module_2_registration_and_login(db):
    """Test user registration, duplicate prevention, and login."""
    test_email = "testfounder_flow@startup.io"

    # Cleanup if exists from previous test run
    existing = db.query(models.User).filter(models.User.email == test_email).first()
    if existing:
        db.delete(existing)
        db.commit()

    # Register
    reg_payload = {
        "email": test_email,
        "password": "StrongPassword123",
        "company_name": "Acme Innovations",
        "industry": "Fintech",
        "team_size": 35,
        "growth_stage": "Growth",
        "hr_budget_monthly": 10000.0,
        "location": "Bangalore",
    }
    resp = client.post("/api/auth/register", json=reg_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["company_name"] == "Acme Innovations"
    user_id = data["user_id"]
    startup_id = data["startup_id"]

    # Duplicate registration should fail
    resp_dup = client.post("/api/auth/register", json=reg_payload)
    assert resp_dup.status_code == 400

    # Login with valid password
    login_resp = client.post("/api/auth/login", json={"email": test_email, "password": "StrongPassword123"})
    assert login_resp.status_code == 200
    assert login_resp.json()["user_id"] == user_id

    # Login with invalid password
    bad_login = client.post("/api/auth/login", json={"email": test_email, "password": "WrongPassword"})
    assert bad_login.status_code == 401


def test_module_2_forgot_and_reset_password(db):
    """Test secure token generation, verification, and password reset."""
    test_email = "testfounder_flow@startup.io"

    # Request password reset
    forgot_resp = client.post("/api/auth/forgot-password", json={"email": test_email})
    assert forgot_resp.status_code == 200
    forgot_data = forgot_resp.json()
    assert "instructions" in forgot_data["message"].lower()

    # Find the token in the database
    user = db.query(models.User).filter(models.User.email == test_email).first()
    token_record = db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.user_id == user.id,
        models.PasswordResetToken.is_used == False,
    ).order_by(models.PasswordResetToken.id.desc()).first()
    assert token_record is not None
    token = token_record.token

    # Verify token endpoint
    verify_resp = client.get(f"/api/auth/verify-reset-token?token={token}")
    assert verify_resp.status_code == 200
    assert verify_resp.json()["valid"] is True
    assert verify_resp.json()["email"] == test_email

    # Reset password with valid token
    new_pw = "BrandNewPassword456"
    reset_resp = client.post("/api/auth/reset-password", json={"token": token, "new_password": new_pw})
    assert reset_resp.status_code == 200

    # Confirm token is marked as used
    db.refresh(token_record)
    assert token_record.is_used is True

    # Confirm reused token is rejected
    reuse_resp = client.get(f"/api/auth/verify-reset-token?token={token}")
    assert reuse_resp.status_code == 200
    assert reuse_resp.json()["valid"] is False

    # Confirm user can now login with new password
    login_new = client.post("/api/auth/login", json={"email": test_email, "password": new_pw})
    assert login_new.status_code == 200


def test_module_2_startup_profile_update(db):
    """Test reading and updating startup constraints (team size, budget)."""
    user = db.query(models.User).filter(models.User.email == "testfounder_flow@startup.io").first()
    startup = user.startup

    # Update team size and budget
    update_payload = {
        "team_size": 42,
        "hr_budget_monthly": 12000.0,
        "location": "Mumbai",
    }
    put_resp = client.put(f"/api/startups/{startup.id}", json=update_payload)
    assert put_resp.status_code == 200
    updated_data = put_resp.json()
    assert updated_data["team_size"] == 42
    assert updated_data["hr_budget_monthly"] == 12000.0
    assert updated_data["location"] == "Mumbai"


def test_module_3_5_6_audit_questionnaire_and_scoring(db):
    """Test questionnaire retrieval, answers submission, score calculation, and gap detection."""
    # 1. Fetch questions
    q_resp = client.get("/api/audit/questions")
    assert q_resp.status_code == 200
    questions = q_resp.json()
    assert len(questions) == 30

    # 2. Select option index 1 (basic manual process, score ~35-40) for all questions
    answers = [
        {"question_id": q["id"], "selected_option_id": q["options"][1]["id"]}
        for q in questions
    ]

    user = db.query(models.User).filter(models.User.email == "testfounder_flow@startup.io").first()
    startup = user.startup

    submit_resp = client.post("/api/audit/submit", json={
        "startup_id": startup.id,
        "answers": answers,
    })
    assert submit_resp.status_code == 200
    res_data = submit_resp.json()
    audit_id = res_data["audit_id"]

    assert "overall_score" in res_data
    assert "status" in res_data
    assert len(res_data["category_scores"]) == 6

    # In our manual-option test, categories score < 60, so gaps should be detected
    high_or_med_gaps = [cs for cs in res_data["category_scores"] if cs["priority"] in ("HIGH", "MEDIUM")]
    assert len(high_or_med_gaps) > 0


def test_module_8_recommendations(db):
    """Test tool recommendations ranking with budget and team size fit."""
    user = db.query(models.User).filter(models.User.email == "testfounder_flow@startup.io").first()
    startup = user.startup
    latest_audit = startup.audits[0]

    rec_resp = client.get(f"/api/recommendations/{latest_audit.id}")
    assert rec_resp.status_code == 200
    recs = rec_resp.json()
    assert len(recs) > 0

    top_rec = recs[0]
    assert "tool_name" in top_rec
    assert "overall_fit" in top_rec
    assert top_rec["overall_fit"] > 0
    assert "reason" in top_rec


def test_module_10_pdf_report_generation(db):
    """Test that ReportLab generates a valid PDF report binary."""
    user = db.query(models.User).filter(models.User.email == "testfounder_flow@startup.io").first()
    startup = user.startup
    latest_audit = startup.audits[0]

    pdf_resp = client.get(f"/api/reports/{latest_audit.id}/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert pdf_resp.content.startswith(b"%PDF")
    assert len(pdf_resp.content) > 1000
