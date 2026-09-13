"""
FastAPI entry point.

Run with:
    uvicorn backend.main:app --reload
"""
from fastapi import FastAPI
from backend.api import audit, recommendations, tools, reports, auth, startups

app = FastAPI(
    title="HR-Tech Advisor API",
    description="AI-Based Digital HR Audit Tool — backend services",
    version="0.1.0",
)

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(startups.router, prefix="/api/startups", tags=["Startups"])
app.include_router(audit.router, prefix="/api/audit", tags=["Audit"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["Recommendations"])
app.include_router(tools.router, prefix="/api/tools", tags=["HR Tools"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])


@app.get("/")
def health_check():
    return {"status": "ok", "service": "HR-Tech Advisor API"}
