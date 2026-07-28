"""RFM-style behavioral feature engineering.

Pulls Customer/Visit/LineItem/Product rows into pandas, computes raw behavioral
features per customer (recency, frequency, monetary, diversity, channel mix,
spend consistency), then min-max normalizes each into a 0-100 "sub-score" relative
to the current population. app/scoring.py combines these sub-scores per the weighted
rubric in app/personas.py.

Population-relative normalization (rather than fixed absolute thresholds) is a
deliberate choice: there's no external ground truth for what "high frequency" means
for an arbitrary taproom, so scores are always relative to the customers in the
current dataset -- consistent with how the real nightly job this project reimplements
also had to reason about behavior without hardcoded absolute cutoffs.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
from sqlmodel import Session, select

from app.models import Customer, LineItem, Product, Visit

RAW_FEATURE_COLUMNS = [
    "recency_days", "frequency", "tenure_days", "total_spend", "avg_ticket",
    "style_diversity", "event_ratio", "spend_cv",
]


def _load_frames(session: Session) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    customers = pd.DataFrame([c.model_dump() for c in session.exec(select(Customer)).all()])
    visits = pd.DataFrame([v.model_dump() for v in session.exec(select(Visit)).all()])
    line_items = pd.DataFrame([li.model_dump() for li in session.exec(select(LineItem)).all()])
    products = pd.DataFrame([p.model_dump() for p in session.exec(select(Product)).all()])
    return customers, visits, line_items, products


def _minmax_scale(series: pd.Series, invert: bool = False) -> pd.Series:
    lo, hi = series.min(), series.max()
    if hi - lo < 1e-9:
        return pd.Series(50.0, index=series.index)
    scaled = (series - lo) / (hi - lo)
    if invert:
        scaled = 1 - scaled
    return (scaled * 100).round(2)


def compute_customer_features(session: Session, now: datetime | None = None) -> pd.DataFrame:
    """Returns a DataFrame indexed by customer_id with raw + normalized (0-100) features.

    Empty dataset returns an empty DataFrame with the expected columns (no crash).
    """
    now = now or datetime.now(timezone.utc).replace(tzinfo=None)
    customers, visits, line_items, products = _load_frames(session)

    score_columns = [
        "recency_score", "frequency_score", "tenure_score", "total_spend_score",
        "avg_ticket_score", "style_diversity_score", "event_ratio_score",
        "consistency_score", "low_frequency_score",
    ]
    if customers.empty:
        return pd.DataFrame(columns=["display_name", *RAW_FEATURE_COLUMNS, *score_columns])

    visits["visited_at"] = pd.to_datetime(visits["visited_at"])

    visit_agg = visits.groupby("customer_id").agg(
        frequency=("id", "count"),
        total_spend=("total_amount", "sum"),
        last_visit_at=("visited_at", "max"),
        first_visit_at=("visited_at", "min"),
        spend_mean=("total_amount", "mean"),
        spend_std=("total_amount", "std"),
    )
    visit_agg["avg_ticket"] = visit_agg["total_spend"] / visit_agg["frequency"]
    visit_agg["recency_days"] = (pd.Timestamp(now) - visit_agg["last_visit_at"]).dt.days
    visit_agg["tenure_days"] = (visit_agg["last_visit_at"] - visit_agg["first_visit_at"]).dt.days
    spend_cv_denominator = visit_agg["spend_mean"].replace(0, pd.NA)
    visit_agg["spend_cv"] = (visit_agg["spend_std"].fillna(0.0) / spend_cv_denominator).fillna(0.0)

    is_event = (visits["channel"] == "event").astype(float)
    event_ratio = visits.assign(is_event=is_event).groupby("customer_id")["is_event"].mean()
    visit_agg["event_ratio"] = event_ratio

    if not line_items.empty:
        items_with_style = line_items.merge(
            products[["id", "style_label"]], left_on="product_id", right_on="id", suffixes=("", "_product")
        )
        items_with_visit = items_with_style.merge(
            visits[["id", "customer_id"]], left_on="visit_id", right_on="id", suffixes=("", "_visit")
        )
        style_diversity = (
            items_with_visit.dropna(subset=["style_label"])
            .groupby("customer_id")["style_label"]
            .nunique()
        )
        visit_agg["style_diversity"] = style_diversity
    visit_agg["style_diversity"] = visit_agg.get("style_diversity", pd.Series(dtype=float)).fillna(0)

    features = customers.set_index("id").join(visit_agg[RAW_FEATURE_COLUMNS])
    features[RAW_FEATURE_COLUMNS] = features[RAW_FEATURE_COLUMNS].fillna(0)
    features.index.name = "customer_id"

    features["recency_score"] = _minmax_scale(features["recency_days"], invert=True)
    features["frequency_score"] = _minmax_scale(features["frequency"])
    features["low_frequency_score"] = _minmax_scale(features["frequency"], invert=True)
    features["tenure_score"] = _minmax_scale(features["tenure_days"])
    features["total_spend_score"] = _minmax_scale(features["total_spend"])
    features["avg_ticket_score"] = _minmax_scale(features["avg_ticket"])
    features["style_diversity_score"] = _minmax_scale(features["style_diversity"])
    features["event_ratio_score"] = _minmax_scale(features["event_ratio"])
    features["consistency_score"] = _minmax_scale(features["spend_cv"], invert=True)

    return features[["display_name", *RAW_FEATURE_COLUMNS, *score_columns]]
