from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.database import get_session
from app.models import Customer, PersonaScore
from app.personas import PERSONAS_BY_KEY
from app.schemas import CustomerDetailOut, CustomerSummaryOut, PersonaScoreOut

router = APIRouter(prefix="/api/customers", tags=["customers"])


def _top_score(scores: list[PersonaScore]) -> Optional[PersonaScore]:
    return max(scores, key=lambda s: s.score) if scores else None


@router.get("", response_model=list[CustomerSummaryOut])
def list_customers(
    persona: Optional[str] = Query(None, description="Filter/sort by this persona key"),
    sort: str = Query("score_desc", pattern="^(score_desc|score_asc|name_asc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    session: Session = Depends(get_session),
) -> list[CustomerSummaryOut]:
    if persona and persona not in PERSONAS_BY_KEY:
        raise HTTPException(status_code=404, detail=f"Unknown persona '{persona}'")

    customers = session.exec(select(Customer)).all()
    scores_by_customer: dict[int, list[PersonaScore]] = {}
    for score in session.exec(select(PersonaScore)).all():
        scores_by_customer.setdefault(score.customer_id, []).append(score)

    rows: list[CustomerSummaryOut] = []
    for customer in customers:
        cust_scores = scores_by_customer.get(customer.id, [])
        top = _top_score(cust_scores)
        filtered_score = None
        if persona:
            match = next((s for s in cust_scores if s.persona_key == persona), None)
            filtered_score = match.score if match else 0.0

        rows.append(
            CustomerSummaryOut(
                customer_id=customer.id,
                display_name=customer.display_name,
                top_persona_key=top.persona_key if top else None,
                top_persona_name=PERSONAS_BY_KEY[top.persona_key].name if top else None,
                top_persona_score=top.score if top else 0.0,
                filtered_persona_score=filtered_score,
                last_visit_at=customer.last_visit_at,
            )
        )

    def sort_key(row: CustomerSummaryOut) -> float | str:
        if sort == "name_asc":
            return row.display_name
        return row.filtered_persona_score if persona else row.top_persona_score

    rows.sort(key=sort_key, reverse=(sort == "score_desc"))

    start = (page - 1) * page_size
    return rows[start : start + page_size]


@router.get("/{customer_id}", response_model=CustomerDetailOut)
def get_customer(customer_id: int, session: Session = Depends(get_session)) -> CustomerDetailOut:
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    scores = session.exec(select(PersonaScore).where(PersonaScore.customer_id == customer_id)).all()
    persona_scores = [
        PersonaScoreOut(
            persona_key=s.persona_key,
            persona_name=PERSONAS_BY_KEY[s.persona_key].name,
            score=s.score,
            breakdown=json.loads(s.breakdown_json),
        )
        for s in scores
    ]
    persona_scores.sort(key=lambda p: p.score, reverse=True)

    return CustomerDetailOut(
        customer_id=customer.id,
        display_name=customer.display_name,
        first_visit_at=customer.first_visit_at,
        last_visit_at=customer.last_visit_at,
        persona_scores=persona_scores,
    )
