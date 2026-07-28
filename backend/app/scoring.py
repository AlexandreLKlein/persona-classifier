"""Persona scoring engine.

Combines the normalized behavioral sub-scores from app/features.py into a single
0-100 score per (customer, persona) using the weighted rubric in app/personas.py,
plus a per-feature contribution breakdown for explainability.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pandas as pd
from sqlmodel import Session, delete

from app.features import compute_customer_features
from app.models import PersonaScore
from app.personas import PERSONAS


def score_customers(features: pd.DataFrame) -> dict[int, dict[str, dict]]:
    """Returns {customer_id: {persona_key: {"score": float, "breakdown": {sub_score: contribution}}}}."""
    results: dict[int, dict[str, dict]] = {}
    for customer_id, row in features.iterrows():
        persona_results: dict[str, dict] = {}
        for persona in PERSONAS:
            breakdown = {}
            total = 0.0
            for sub_score_name, weight in persona.weights.items():
                contribution = round(float(row[sub_score_name]) * weight, 2)
                breakdown[sub_score_name] = contribution
                total += contribution
            persona_results[persona.key] = {"score": round(total, 2), "breakdown": breakdown}
        results[customer_id] = persona_results
    return results


def recompute_all_scores(session: Session) -> int:
    """Recomputes features + scores for every customer and overwrites PersonaScore rows.

    Returns the number of (customer, persona) score rows written.
    """
    features = compute_customer_features(session)
    results = score_customers(features)

    session.exec(delete(PersonaScore))
    session.commit()

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    count = 0
    for customer_id, persona_scores in results.items():
        for persona_key, result in persona_scores.items():
            session.add(
                PersonaScore(
                    customer_id=int(customer_id),
                    persona_key=persona_key,
                    score=result["score"],
                    breakdown_json=json.dumps(result["breakdown"]),
                    computed_at=now,
                )
            )
            count += 1
    session.commit()
    return count
