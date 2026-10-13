"""Read a startup's profile (used by the Django dashboard)."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.database import get_db
from database import models

router = APIRouter()


@router.get("/{startup_id}")
def get_startup(startup_id: int, db: Session = Depends(get_db)):
    startup = db.query(models.Startup).get(startup_id)
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
    return {
        "id": startup.id,
        "company_name": startup.company_name,
        "industry": startup.industry,
        "team_size": startup.team_size,
        "growth_stage": startup.growth_stage,
        "hr_budget_monthly": startup.hr_budget_monthly,
        "location": startup.location,
        "contact_email": startup.contact_email,
    }


class StartupUpdatePayload(BaseModel):
    company_name: Optional[str] = None
    industry: Optional[str] = None
    team_size: Optional[int] = None
    growth_stage: Optional[str] = None
    hr_budget_monthly: Optional[float] = None
    location: Optional[str] = None
    contact_email: Optional[str] = None


@router.put("/{startup_id}")
def update_startup(startup_id: int, payload: StartupUpdatePayload, db: Session = Depends(get_db)):
    startup = db.query(models.Startup).get(startup_id)
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")

    if payload.company_name is not None:
        startup.company_name = payload.company_name
    if payload.industry is not None:
        startup.industry = payload.industry
    if payload.team_size is not None:
        startup.team_size = payload.team_size
    if payload.growth_stage is not None:
        startup.growth_stage = payload.growth_stage
    if payload.hr_budget_monthly is not None:
        startup.hr_budget_monthly = payload.hr_budget_monthly
    if payload.location is not None:
        startup.location = payload.location
    if payload.contact_email is not None:
        startup.contact_email = payload.contact_email

    db.commit()
    db.refresh(startup)
    return {
        "id": startup.id,
        "company_name": startup.company_name,
        "industry": startup.industry,
        "team_size": startup.team_size,
        "growth_stage": startup.growth_stage,
        "hr_budget_monthly": startup.hr_budget_monthly,
        "location": startup.location,
        "contact_email": startup.contact_email,
    }

