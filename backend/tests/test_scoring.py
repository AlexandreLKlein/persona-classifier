from __future__ import annotations

import pandas as pd

from app.personas import PERSONAS_BY_KEY
from app.scoring import score_customers

ALL_SUB_SCORES = [
    "recency_score", "frequency_score", "tenure_score", "total_spend_score",
    "avg_ticket_score", "style_diversity_score", "event_ratio_score",
    "consistency_score", "low_frequency_score",
]


def _row(**overrides) -> dict:
    row = {col: 0.0 for col in ALL_SUB_SCORES}
    row.update(overrides)
    return row


def test_perfect_explorer_scores_near_100_on_explorer():
    features = pd.DataFrame(
        {
            1: _row(style_diversity_score=100.0, event_ratio_score=100.0, frequency_score=100.0),
            2: _row(),  # a customer who scores zero on every dimension
        }
    ).T
    features.index.name = "customer_id"

    results = score_customers(features)

    explorer_weights = PERSONAS_BY_KEY["explorer"].weights
    expected_explorer_score = sum(100.0 * w for w in explorer_weights.values())
    assert results[1]["explorer"]["score"] == round(expected_explorer_score, 2)
    assert results[1]["explorer"]["score"] > results[1]["regular"]["score"]
    assert results[2]["explorer"]["score"] == 0.0

    breakdown = results[1]["explorer"]["breakdown"]
    assert set(breakdown.keys()) == set(explorer_weights.keys())
    assert breakdown["style_diversity_score"] == round(100.0 * explorer_weights["style_diversity_score"], 2)


def test_all_five_personas_are_scored_for_every_customer():
    features = pd.DataFrame({1: _row()}).T
    features.index.name = "customer_id"

    results = score_customers(features)

    assert set(results[1].keys()) == {"regular", "explorer", "big_tab", "event_chaser", "quiet_sipper"}
