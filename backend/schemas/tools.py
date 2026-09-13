"""Pydantic schemas for the HR Tools API."""
from pydantic import BaseModel
from typing import Optional


class HRToolOut(BaseModel):
    id: int
    name: str
    category_id: int
    description: Optional[str] = None
    monthly_cost: Optional[float] = None
    min_team_size: int
    max_team_size: int
    features: Optional[str] = None
    website: Optional[str] = None

    class Config:
        from_attributes = True


class HRToolCreate(BaseModel):
    name: str
    category_id: int
    description: Optional[str] = None
    monthly_cost: Optional[float] = None
    min_team_size: int = 0
    max_team_size: int = 100000
    features: Optional[str] = None
    website: Optional[str] = None


class HRToolUpdate(BaseModel):
    """All fields optional — only the ones provided get changed (PATCH semantics)."""
    name: Optional[str] = None
    category_id: Optional[int] = None
    description: Optional[str] = None
    monthly_cost: Optional[float] = None
    min_team_size: Optional[int] = None
    max_team_size: Optional[int] = None
    features: Optional[str] = None
    website: Optional[str] = None
