from __future__ import annotations

from datetime import datetime, timedelta

from app.features import compute_customer_features
from app.models import Customer, LineItem, Product, Visit


def _mk_customer(session, name, first_visit_at, last_visit_at):
    customer = Customer(
        display_name=name, first_visit_at=first_visit_at, last_visit_at=last_visit_at, created_at=first_visit_at
    )
    session.add(customer)
    session.commit()
    session.refresh(customer)
    return customer


def _mk_visit(session, customer_id, visited_at, channel, total_amount):
    visit = Visit(customer_id=customer_id, visited_at=visited_at, channel=channel, total_amount=total_amount)
    session.add(visit)
    session.commit()
    session.refresh(visit)
    return visit


def test_features_differentiate_frequent_recent_from_rare_old(session):
    now = datetime(2026, 1, 1)

    beer_a = Product(name="IPA", category="beer", style_label="IPA", unit_price=8.0)
    beer_b = Product(name="Stout", category="beer", style_label="Stout", unit_price=8.0)
    session.add(beer_a)
    session.add(beer_b)
    session.commit()
    session.refresh(beer_a)
    session.refresh(beer_b)

    # Customer A: 10 visits spanning the last 90 days, most recent visit is exactly "now",
    # alternating between two beer styles.
    customer_a = _mk_customer(session, "Frequent Recent", now - timedelta(days=90), now)
    for i in range(10):
        visited_at = now - timedelta(days=90 - i * 10)
        visit = _mk_visit(session, customer_a.id, visited_at, "taproom", 20.0)
        product = beer_a if i % 2 == 0 else beer_b
        session.add(LineItem(visit_id=visit.id, product_id=product.id, quantity=1, unit_price=8.0))
    session.commit()

    # Customer B: 2 visits, both long ago, always the same beer.
    customer_b = _mk_customer(session, "Rare Old", now - timedelta(days=210), now - timedelta(days=200))
    for visited_at in [now - timedelta(days=210), now - timedelta(days=200)]:
        visit = _mk_visit(session, customer_b.id, visited_at, "taproom", 8.0)
        session.add(LineItem(visit_id=visit.id, product_id=beer_a.id, quantity=1, unit_price=8.0))
    session.commit()

    features = compute_customer_features(session, now=now)

    assert features.loc[customer_a.id, "frequency"] == 10
    assert features.loc[customer_b.id, "frequency"] == 2
    assert features.loc[customer_a.id, "recency_days"] == 0
    assert features.loc[customer_b.id, "recency_days"] == 200

    # Population-relative scores: A should clearly outrank B on recency and frequency,
    # and B (the sparse customer) should score higher on the *inverse* frequency sub-score.
    assert features.loc[customer_a.id, "recency_score"] > features.loc[customer_b.id, "recency_score"]
    assert features.loc[customer_a.id, "frequency_score"] > features.loc[customer_b.id, "frequency_score"]
    assert features.loc[customer_b.id, "low_frequency_score"] > features.loc[customer_a.id, "low_frequency_score"]

    # A drinks 2 distinct styles, B drinks 1 -- A should score higher on diversity.
    assert features.loc[customer_a.id, "style_diversity"] == 2
    assert features.loc[customer_b.id, "style_diversity"] == 1
    assert features.loc[customer_a.id, "style_diversity_score"] > features.loc[customer_b.id, "style_diversity_score"]


def test_features_empty_dataset_returns_empty_frame(session):
    features = compute_customer_features(session)
    assert features.empty
    assert "recency_score" in features.columns
