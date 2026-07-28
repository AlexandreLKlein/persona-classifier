"""Pydantic API response schemas -- kept separate from the SQLModel table models in
models.py so the API contract can evolve independently of the storage schema."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PersonaDefinitionOut(BaseModel):
    key: str
    name: str
    description: str
    weights: dict[str, float]


class PersonaScoreOut(BaseModel):
    persona_key: str
    persona_name: str
    score: float
    breakdown: dict[str, float]


class CustomerSummaryOut(BaseModel):
    customer_id: int
    display_name: str
    top_persona_key: Optional[str] = None
    top_persona_name: Optional[str] = None
    top_persona_score: float
    filtered_persona_score: Optional[float] = None
    last_visit_at: datetime


class CustomerDetailOut(BaseModel):
    customer_id: int
    display_name: str
    first_visit_at: datetime
    last_visit_at: datetime
    persona_scores: list[PersonaScoreOut]


class LeaderboardEntryOut(BaseModel):
    customer_id: int
    display_name: str
    score: float
    breakdown: dict[str, float]


class RecomputeResultOut(BaseModel):
    persona_scores_written: int
