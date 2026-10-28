"""Validated response schema for AI-generated audit guidance."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AuditAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str = Field(min_length=1, max_length=100)
    priority: Literal["HIGH", "MEDIUM", "LOW"]
    explanation: str = Field(min_length=1, max_length=500)
    next_step: str = Field(min_length=1, max_length=500)


class AuditExplanation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1, max_length=1000)
    actions: list[AuditAction] = Field(max_length=6)
