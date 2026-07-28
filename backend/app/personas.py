"""Persona taxonomy and scoring rubric.

Original design for this project -- five persona archetypes with weights I designed
from scratch, independent of any real system. See README.md for why that matters here.

Each persona is a weighted combination of normalized (0-100) behavioral sub-scores
produced by app/features.py. Weights are documented per-persona so the API can expose
the rubric verbatim (GET /api/personas) -- explainability is a first-class feature,
not an afterthought.
"""
from __future__ import annotations

from typing import NamedTuple


class PersonaDefinition(NamedTuple):
    key: str
    name: str
    description: str
    weights: dict[str, float]  # sub-score name -> weight, should sum to 1.0


PERSONAS: list[PersonaDefinition] = [
    PersonaDefinition(
        key="regular",
        name="The Regular",
        description="Visits often and recently -- the backbone of steady foot traffic.",
        weights={"recency_score": 0.4, "frequency_score": 0.4, "tenure_score": 0.2},
    ),
    PersonaDefinition(
        key="explorer",
        name="The Explorer",
        description="Tries a wide range of styles and categories rather than ordering the same thing.",
        weights={"style_diversity_score": 0.6, "event_ratio_score": 0.2, "frequency_score": 0.2},
    ),
    PersonaDefinition(
        key="big_tab",
        name="The Big Tab",
        description="Spends well above average per visit and in total.",
        weights={"avg_ticket_score": 0.5, "total_spend_score": 0.5},
    ),
    PersonaDefinition(
        key="event_chaser",
        name="The Event Chaser",
        description="Shows up mainly for ticketed events rather than regular taproom visits.",
        weights={"event_ratio_score": 0.7, "frequency_score": 0.3},
    ),
    PersonaDefinition(
        key="quiet_sipper",
        name="The Quiet Sipper",
        description="Long-tenured, infrequent, and consistent -- low-key loyalty over a long time span.",
        weights={"tenure_score": 0.35, "low_frequency_score": 0.35, "consistency_score": 0.3},
    ),
]

PERSONAS_BY_KEY: dict[str, PersonaDefinition] = {p.key: p for p in PERSONAS}
