from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from app.api import admin, customers, personas
from app.data.seed import seed_database
from app.database import engine, init_db
from app.models import Customer


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    with Session(engine) as session:
        has_data = session.exec(select(Customer).limit(1)).first() is not None
        if not has_data:
            seed_database(session)
    yield


app = FastAPI(
    title="Persona Classifier API",
    description=(
        "A from-scratch, synthetic-data reimplementation of a taproom customer-scoring "
        "job -- see README for the story and the IP guardrail this project follows."
    ),
    lifespan=lifespan,
)

allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(customers.router)
app.include_router(personas.router)
app.include_router(admin.router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
