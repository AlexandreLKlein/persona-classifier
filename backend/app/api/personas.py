from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.database import get_session
from app.models import Customer, PersonaScore
from app.personas import PERSONAS, PERSONAS_BY_KEY
from app.schemas import LeaderboardEntryOut, PersonaDefinitionOut

router = APIRouter(prefix="/api/personas", tags=["personas"])


@router.get("", response_model=list[PersonaDefinitionOut])
def list_personas() -> list[PersonaDefinitionOut]:
    return [
        PersonaDefinitionOut(key=p.key, name=p.name, description=p.description, weights=p.weights) for p in PERSONAS
    ]


@router.get("/{persona_key}/leaderboard", response_model=list[LeaderboardEntryOut])
def persona_leaderboard(
    persona_key: str,
    limit: int = Query(25, ge=1, le=100),
    session: Session = Depends(get_session),
) -> list[LeaderboardEntryOut]:
    if persona_key not in PERSONAS_BY_KEY:
        raise HTTPException(status_code=404, detail=f"Unknown persona '{persona_key}'")

    scores = session.exec(select(PersonaScore).where(PersonaScore.persona_key == persona_key)).all()
    scores.sort(key=lambda s: s.score, reverse=True)
    scores = scores[:limit]

    customers = {c.id: c for c in session.exec(select(Customer)).all()}
    return [
        LeaderboardEntryOut(
            customer_id=s.customer_id,
            display_name=customers[s.customer_id].display_name if s.customer_id in customers else "Unknown",
            score=s.score,
            breakdown=json.loads(s.breakdown_json),
        )
        for s in scores
    ]
