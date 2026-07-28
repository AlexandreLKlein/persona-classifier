"""Seed script: wipes and repopulates the database with a fresh synthetic dataset,
then runs the scoring pipeline so the API has data immediately.

Usage:
    python -m app.data.seed [--seed 42] [--customers 220]
"""
from __future__ import annotations

import argparse
import logging

from sqlmodel import Session, delete

from app.data.generator import generate_dataset
from app.database import engine, init_db
from app.models import Customer, LineItem, PersonaScore, Product, Visit
from app.scoring import recompute_all_scores

logger = logging.getLogger(__name__)


def seed_database(session: Session, seed: int = 42, n_customers: int = 220) -> None:
    logger.info("Wiping existing data...")
    session.exec(delete(PersonaScore))
    session.exec(delete(LineItem))
    session.exec(delete(Visit))
    session.exec(delete(Customer))
    session.exec(delete(Product))
    session.commit()

    logger.info("Generating synthetic dataset (seed=%s, n_customers=%s)...", seed, n_customers)
    dataset = generate_dataset(seed=seed, n_customers=n_customers)

    session.add_all(dataset.products)
    session.commit()
    for product in dataset.products:
        session.refresh(product)

    for generated_customer in dataset.customers:
        customer = Customer(
            display_name=generated_customer.display_name,
            first_visit_at=generated_customer.first_visit_at,
            last_visit_at=generated_customer.last_visit_at,
            created_at=generated_customer.created_at,
        )
        session.add(customer)
        session.commit()
        session.refresh(customer)

        for generated_visit in generated_customer.visits:
            visit = Visit(
                customer_id=customer.id,
                visited_at=generated_visit.visited_at,
                channel=generated_visit.channel,
                total_amount=generated_visit.total_amount,
            )
            session.add(visit)
            session.commit()
            session.refresh(visit)

            for generated_item in generated_visit.items:
                product = dataset.products[generated_item.product_index]
                session.add(
                    LineItem(
                        visit_id=visit.id,
                        product_id=product.id,
                        quantity=generated_item.quantity,
                        unit_price=generated_item.unit_price,
                    )
                )
        session.commit()

    logger.info("Inserted %s customers, %s products.", len(dataset.customers), len(dataset.products))

    logger.info("Running scoring pipeline...")
    count = recompute_all_scores(session)
    logger.info("Wrote %s persona scores.", count)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--customers", type=int, default=220)
    args = parser.parse_args()

    init_db()
    with Session(engine) as session:
        seed_database(session, seed=args.seed, n_customers=args.customers)


if __name__ == "__main__":
    main()
