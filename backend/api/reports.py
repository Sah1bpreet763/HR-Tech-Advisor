"""MODULE 10 API — Digital HR Health Report data (PDF generation comes later)."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from database.database import get_db
from database import models
from backend.services.report_generator import generate_audit_pdf

router = APIRouter()


@router.get("/{audit_id}")
def get_report_data(audit_id: int, db: Session = Depends(get_db)):
    """
    Returns the structured data a PDF report would be built from, and
    logs a Report row so there's a record of when this was generated.
    Actual PDF rendering (ReportLab) is added in Phase 8 of the roadmap;
    `file_path` stays null until then.
    """
    audit = db.query(models.Audit).get(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    db.add(models.Report(audit_id=audit_id, format="json", file_path=None))
    db.commit()

    return {
        "startup": audit.startup.company_name,
        "overall_score": audit.overall_score,
        "category_scores": [
            {"category": cs.category.name, "score": cs.score, "priority": cs.priority}
            for cs in audit.scores
        ],
        "recommendations": [
            {"tool_name": rec.tool.name, "fit_score": rec.fit_score, "reason": rec.reason}
            for rec in audit.recommendations
        ],
    }


@router.get("/{audit_id}/pdf")
def get_report_pdf(audit_id: int, db: Session = Depends(get_db)):
    """
    Generates and returns an executive PDF report binary via ReportLab.
    """
    audit = db.query(models.Audit).get(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    if audit.status != "completed":
        raise HTTPException(status_code=409, detail="Audit is not yet completed")

    pdf_bytes = generate_audit_pdf(db, audit)

    # Log report generation in reports table
    db.add(models.Report(audit_id=audit_id, format="pdf", file_path=None))
    db.commit()

    filename = f"HR_Health_Report_{audit.startup.company_name.replace(' ', '_')}_{audit.id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

