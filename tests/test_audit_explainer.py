import json

import pytest
import requests
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from database import models
from database.database import Base, get_db


@pytest.fixture
def audit_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    user = models.User(email="explainer-test@example.com", hashed_password="test-hash")
    db.add(user)
    db.flush()
    startup = models.Startup(user_id=user.id, company_name="Test Startup")
    db.add(startup)
    db.flush()
    category = models.Category(name="Recruitment")
    db.add(category)
    db.flush()
    audit = models.Audit(
        startup_id=startup.id,
        status="completed",
        overall_score=42.5,
    )
    db.add(audit)
    db.flush()
    db.add(models.CategoryScore(
        audit_id=audit.id,
        category_id=category.id,
        score=35,
        gap_description="Recruitment processes need improvement.",
        priority="HIGH",
    ))
    db.commit()
    audit_id = audit.id
    startup_id = startup.id
    db.close()

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app), audit_id, startup_id
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


class MockGeminiResponse:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        return None

    def json(self):
        return {
            "candidates": [
                {"content": {"parts": [{"text": json.dumps(self.content)}]}}
            ]
        }


def test_explainer_returns_grounded_advice_and_sends_only_aggregate_data(
    audit_client, monkeypatch
):
    client, audit_id, startup_id = audit_client
    monkeypatch.setenv("AI_API_KEY", "test-key")
    monkeypatch.setenv("AI_MODEL", "gemini-2.5-flash")
    captured_request = {}

    def mock_post(url, **kwargs):
        captured_request["url"] = url
        captured_request.update(kwargs)
        return MockGeminiResponse({
            "summary": "Recruitment is the highest-priority area to improve.",
            "actions": [
                {
                    "category": "Recruitment",
                    "priority": "HIGH",
                    "explanation": "The audit score identifies a gap.",
                    "next_step": "Document the steps used to review applicants.",
                }
            ],
        })

    monkeypatch.setattr("backend.services.ai_advisor.requests.post", mock_post)
    response = client.post(
        f"/api/audit/{audit_id}/explanation",
        params={"startup_id": startup_id},
    )

    assert response.status_code == 200
    assert response.json()["actions"][0]["category"] == "Recruitment"
    assert captured_request["url"].endswith(
        "/v1beta/models/gemini-2.5-flash:generateContent"
    )
    assert captured_request["headers"]["x-goog-api-key"] == "test-key"
    assert "Authorization" not in captured_request["headers"]
    assert captured_request["json"]["generationConfig"]["responseMimeType"] == "application/json"
    sent_data = captured_request["json"]["contents"][0]["parts"][0]["text"]
    assert "Recruitment" in sent_data
    assert "Test Startup" not in sent_data
    assert "explainer-test@example.com" not in sent_data


def test_explainer_rejects_an_audit_from_another_startup(audit_client, monkeypatch):
    client, audit_id, _ = audit_client
    monkeypatch.setenv("AI_API_KEY", "test-key")

    def unexpected_call(*args, **kwargs):
        pytest.fail("AI provider should not be called for a mismatched startup")

    monkeypatch.setattr("backend.services.ai_advisor.requests.post", unexpected_call)
    response = client.post(
        f"/api/audit/{audit_id}/explanation",
        params={"startup_id": 9999},
    )

    assert response.status_code == 404


def test_explainer_reports_missing_configuration(audit_client, monkeypatch):
    client, audit_id, startup_id = audit_client
    monkeypatch.delenv("AI_API_KEY", raising=False)

    response = client.post(
        f"/api/audit/{audit_id}/explanation",
        params={"startup_id": startup_id},
    )

    assert response.status_code == 503
    assert "AI_API_KEY" in response.json()["detail"]


def test_explainer_reports_provider_outage(audit_client, monkeypatch):
    client, audit_id, startup_id = audit_client
    monkeypatch.setenv("AI_API_KEY", "test-key")

    def raise_timeout(*args, **kwargs):
        raise requests.Timeout("provider timed out")

    monkeypatch.setattr("backend.services.ai_advisor.requests.post", raise_timeout)
    response = client.post(
        f"/api/audit/{audit_id}/explanation",
        params={"startup_id": startup_id},
    )

    assert response.status_code == 503


@pytest.mark.parametrize(
    ("provider_status", "expected_detail"),
    [
        (403, "Google Gemini rejected the API key"),
        (429, "quota or rate limit"),
    ],
)
def test_explainer_reports_gemini_configuration_and_quota_errors(
    audit_client, monkeypatch, provider_status, expected_detail
):
    client, audit_id, startup_id = audit_client
    monkeypatch.setenv("AI_API_KEY", "test-key")
    provider_response = requests.Response()
    provider_response.status_code = provider_status
    provider_response.url = "https://generativelanguage.googleapis.com/"
    provider_response._content = b'{"error":{"message":"provider error"}}'
    monkeypatch.setattr(
        "backend.services.ai_advisor.requests.post",
        lambda *args, **kwargs: provider_response,
    )

    response = client.post(
        f"/api/audit/{audit_id}/explanation",
        params={"startup_id": startup_id},
    )

    assert response.status_code == 503
    assert expected_detail in response.json()["detail"]


def test_explainer_rejects_actions_not_supported_by_audit_scores(
    audit_client, monkeypatch
):
    client, audit_id, startup_id = audit_client
    monkeypatch.setenv("AI_API_KEY", "test-key")
    monkeypatch.setattr(
        "backend.services.ai_advisor.requests.post",
        lambda *args, **kwargs: MockGeminiResponse({
            "summary": "An unsupported recommendation.",
            "actions": [
                {
                    "category": "Payroll",
                    "priority": "HIGH",
                    "explanation": "Unsupported category.",
                    "next_step": "Take an action.",
                }
            ],
        }),
    )

    response = client.post(
        f"/api/audit/{audit_id}/explanation",
        params={"startup_id": startup_id},
    )

    assert response.status_code == 502
