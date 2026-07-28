"""Synthetic dataset generator.

Everything here is fabricated. No real customer, visit, or purchase data is used or
referenced anywhere in this project -- see README.md's "Why synthetic data" section.

Customers are generated with a bias toward one of the five persona archetypes (plus a
noisy "mixed" long tail) so the demo has believable, discoverable examples of each
persona rather than a flat random blob. The scoring engine (app/scoring.py) never sees
these archetype labels -- it only sees behavioral features, exactly like the real
pipeline this project reimplements would.

Returns plain dataclasses rather than persisted SQLModel rows, since customers/visits/
line items need database-assigned foreign keys -- see app/data/seed.py for persistence.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import numpy as np
from faker import Faker

from app.models import Product

ARCHETYPES = ["regular", "explorer", "big_tab", "event_chaser", "quiet_sipper", "mixed"]
ARCHETYPE_WEIGHTS = [0.16, 0.16, 0.16, 0.16, 0.16, 0.20]

BEER_STYLES = [
    "West Coast IPA", "Hazy Pale Ale", "Vienna Lager", "Dry Stout", "Bock",
    "Belgian Witbier", "American Amber", "Fruited Sour", "Pilsner", "Doppelbock",
]
FOOD_ITEMS = ["Burger", "Wood-fired Pizza", "Pretzel Board", "Bratwurst Plate"]
MERCH_ITEMS = ["Taproom T-Shirt", "Branded Glass", "Bottle Opener"]
EVENT_ITEMS = ["Live Music Night", "Brewery Tour", "Trivia Night"]


@dataclass
class GeneratedLineItem:
    product_index: int  # index into SyntheticDataset.products
    quantity: int
    unit_price: float


@dataclass
class GeneratedVisit:
    visited_at: datetime
    channel: str
    total_amount: float
    items: list[GeneratedLineItem] = field(default_factory=list)


@dataclass
class GeneratedCustomer:
    display_name: str
    first_visit_at: datetime
    last_visit_at: datetime
    created_at: datetime
    archetype: str  # generation label only -- never fed into the scoring engine
    visits: list[GeneratedVisit] = field(default_factory=list)


@dataclass
class SyntheticDataset:
    products: list[Product]
    customers: list[GeneratedCustomer]


def _build_product_catalog() -> list[Product]:
    products: list[Product] = []
    for style in BEER_STYLES:
        products.append(
            Product(name=style, category="beer", style_label=style, unit_price=round(random.uniform(7, 12), 2))
        )
    for name in FOOD_ITEMS:
        products.append(Product(name=name, category="food", unit_price=round(random.uniform(10, 22), 2)))
    for name in MERCH_ITEMS:
        products.append(Product(name=name, category="merch", unit_price=round(random.uniform(15, 30), 2)))
    for name in EVENT_ITEMS:
        products.append(Product(name=name, category="event_ticket", unit_price=round(random.uniform(20, 45), 2)))
    return products


def _visit_params_for_archetype(archetype: str, rng: random.Random) -> dict:
    if archetype == "regular":
        return dict(tenure_days=rng.randint(180, 540), recency_days=rng.randint(0, 6), frequency=rng.randint(20, 45))
    if archetype == "explorer":
        return dict(tenure_days=rng.randint(120, 400), recency_days=rng.randint(2, 30), frequency=rng.randint(10, 25))
    if archetype == "big_tab":
        return dict(tenure_days=rng.randint(90, 400), recency_days=rng.randint(2, 30), frequency=rng.randint(8, 20))
    if archetype == "event_chaser":
        return dict(tenure_days=rng.randint(120, 400), recency_days=rng.randint(2, 45), frequency=rng.randint(5, 15))
    if archetype == "quiet_sipper":
        return dict(tenure_days=rng.randint(400, 800), recency_days=rng.randint(5, 90), frequency=rng.randint(3, 9))
    return dict(tenure_days=rng.randint(20, 700), recency_days=rng.randint(0, 120), frequency=rng.randint(1, 15))


def _pick_channel(archetype: str, rng: random.Random) -> str:
    if archetype == "event_chaser":
        return "event" if rng.random() < 0.75 else "taproom"
    return "event" if rng.random() < 0.08 else "taproom"


def _pick_product_indexes(archetype: str, products: list[Product], rng: random.Random) -> list[int]:
    beer_idx = [i for i, p in enumerate(products) if p.category == "beer"]
    non_beer_idx = [i for i, p in enumerate(products) if p.category != "beer"]
    non_event_idx = [i for i, p in enumerate(products) if p.category != "event_ticket"]

    if archetype == "explorer":
        n = min(rng.randint(1, 3), len(beer_idx))
        return rng.sample(beer_idx, k=n)
    if archetype == "big_tab":
        n = rng.randint(3, 6)
        pool = beer_idx + non_beer_idx
        return [rng.choice(pool) for _ in range(n)]
    if archetype == "quiet_sipper":
        favorites = rng.sample(beer_idx, k=min(2, len(beer_idx)))
        n = rng.randint(1, 2)
        return [rng.choice(favorites) for _ in range(n)]

    n = rng.randint(1, 3)
    pool = [i for i in non_event_idx] if archetype != "event_chaser" else beer_idx + non_beer_idx
    pool = pool or beer_idx
    return [rng.choice(pool) for _ in range(n)]


def generate_dataset(seed: int = 42, n_customers: int = 220, now: datetime | None = None) -> SyntheticDataset:
    rng = random.Random(seed)
    np.random.seed(seed)
    fake = Faker()
    Faker.seed(seed)
    now = now or datetime.now(timezone.utc).replace(tzinfo=None)

    products = _build_product_catalog()
    customers: list[GeneratedCustomer] = []

    for _ in range(n_customers):
        archetype = rng.choices(ARCHETYPES, weights=ARCHETYPE_WEIGHTS)[0]
        params = _visit_params_for_archetype(archetype, rng)

        last_visit_at = now - timedelta(days=params["recency_days"])
        first_visit_at = last_visit_at - timedelta(days=params["tenure_days"])
        if first_visit_at >= last_visit_at:
            first_visit_at = last_visit_at - timedelta(days=1)

        customer = GeneratedCustomer(
            display_name=fake.name(),
            first_visit_at=first_visit_at,
            last_visit_at=last_visit_at,
            created_at=first_visit_at,
            archetype=archetype,
        )

        span_seconds = max(int((last_visit_at - first_visit_at).total_seconds()), 1)
        visit_times = sorted(
            first_visit_at + timedelta(seconds=rng.randint(0, span_seconds)) for _ in range(params["frequency"])
        )
        # guarantee at least one visit lands exactly on last_visit_at so recency matches the archetype params
        if visit_times:
            visit_times[-1] = last_visit_at

        for visited_at in visit_times:
            channel = _pick_channel(archetype, rng)
            product_indexes = _pick_product_indexes(archetype, products, rng)

            items: list[GeneratedLineItem] = []
            total = 0.0
            for idx in product_indexes:
                qty = rng.randint(1, 2)
                unit_price = products[idx].unit_price
                total += qty * unit_price
                items.append(GeneratedLineItem(product_index=idx, quantity=qty, unit_price=unit_price))

            if archetype == "quiet_sipper":
                total = total * rng.uniform(0.95, 1.05)  # keep spend tight around a personal average

            customer.visits.append(
                GeneratedVisit(visited_at=visited_at, channel=channel, total_amount=round(total, 2), items=items)
            )

        customers.append(customer)

    return SyntheticDataset(products=products, customers=customers)
