"""
MODULE 7 API — HR Tool database.

Read endpoints are what the Recommendation Engine (Module 8) and the
future dashboard use. Create/update/delete are here so tools can be
managed via the API (e.g. by whoever curates the tool database in
Module 7) without needing raw DB scripts.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from database.database import get_db
from database import models
from backend.schemas.tools import HRToolOut, HRToolCreate, HRToolUpdate

router = APIRouter()


@router.get("/", response_model=List[HRToolOut])
def list_tools(
    category: Optional[str] = Query(None, description="Filter by category name, e.g. 'Attendance'"),
    db: Session = Depends(get_db),
):
    query = db.query(models.HRTool)
    if category:
        query = query.join(models.Category).filter(models.Category.name == category)
    return query.all()


@router.get("/{tool_id}", response_model=HRToolOut)
def get_tool(tool_id: int, db: Session = Depends(get_db)):
    tool = db.query(models.HRTool).get(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool


@router.post("/", response_model=HRToolOut, status_code=201)
def create_tool(payload: HRToolCreate, db: Session = Depends(get_db)):
    category = db.query(models.Category).get(payload.category_id)
    if not category:
        raise HTTPException(status_code=400, detail=f"Category {payload.category_id} does not exist")

    tool = models.HRTool(**payload.model_dump())
    db.add(tool)
    db.commit()
    db.refresh(tool)
    return tool


@router.put("/{tool_id}", response_model=HRToolOut)
def update_tool(tool_id: int, payload: HRToolUpdate, db: Session = Depends(get_db)):
    tool = db.query(models.HRTool).get(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    updates = payload.model_dump(exclude_unset=True)
    if "category_id" in updates:
        category = db.query(models.Category).get(updates["category_id"])
        if not category:
            raise HTTPException(status_code=400, detail=f"Category {updates['category_id']} does not exist")

    for field, value in updates.items():
        setattr(tool, field, value)

    db.commit()
    db.refresh(tool)
    return tool


@router.delete("/{tool_id}", status_code=204)
def delete_tool(tool_id: int, db: Session = Depends(get_db)):
    tool = db.query(models.HRTool).get(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    db.delete(tool)
    db.commit()
    return None
