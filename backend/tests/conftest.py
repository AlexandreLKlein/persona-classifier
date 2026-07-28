from __future__ import annotations

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine


@pytest.fixture()
def engine():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(eng)
    return eng


@pytest.fixture()
def session(engine):
    with Session(engine) as s:
        yield s


@pytest.fixture()
def client(engine, monkeypatch):
    from fastapi.testclient import TestClient

    import app.database as database_module
    import app.main as main_module
    from app.database import get_session
    from app.main import app

    monkeypatch.setattr(database_module, "engine", engine)
    monkeypatch.setattr(main_module, "engine", engine)

    def override_get_session():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
