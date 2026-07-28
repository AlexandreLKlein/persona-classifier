"""SQLModel table definitions.

All data in this schema is synthetic (see app/data/generator.py) — there is no real
customer, visit, or purchase data anywhere in this project. See README.md for why.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    category: str = Field(index=True)  # "beer" | "food" | "merch" | "event_ticket"
    style_label: Optional[str] = None  # free-text, e.g. "West Coast IPA" -- not a BJCP lookup
    unit_price: float


class Customer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    display_name: str
    first_visit_at: datetime
    last_visit_at: datetime
    created_at: datetime


class Visit(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customer.id", index=True)
    visited_at: datetime
    channel: str = Field(default="taproom")  # "taproom" | "event"
    total_amount: float


class LineItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    visit_id: int = Field(foreign_key="visit.id", index=True)
    product_id: int = Field(foreign_key="product.id", index=True)
    quantity: int
    unit_price: float


class PersonaScore(SQLModel, table=True):
    """Cached output of the scoring pipeline -- recomputed via POST /api/admin/recompute."""

    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customer.id", index=True)
    persona_key: str = Field(index=True)
    score: float
    breakdown_json: str  # JSON-encoded {feature_name: contribution} for explainability
    computed_at: datetime
