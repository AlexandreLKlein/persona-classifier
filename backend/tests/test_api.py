from __future__ import annotations

from app.personas import PERSONAS


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_list_personas_returns_all_five(client):
    resp = client.get("/api/personas")
    assert resp.status_code == 200
    body = resp.json()
    assert {p["key"] for p in body} == {p.key for p in PERSONAS}


def test_list_customers_is_seeded_and_scored(client):
    resp = client.get("/api/customers")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) > 0
    assert all(c["top_persona_key"] is not None for c in body)
    # default sort is score_desc
    scores = [c["top_persona_score"] for c in body]
    assert scores == sorted(scores, reverse=True)


def test_get_customer_detail_has_all_persona_scores(client):
    customers = client.get("/api/customers").json()
    customer_id = customers[0]["customer_id"]

    resp = client.get(f"/api/customers/{customer_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["persona_scores"]) == len(PERSONAS)
    assert body["persona_scores"] == sorted(body["persona_scores"], key=lambda p: p["score"], reverse=True)


def test_get_unknown_customer_is_404(client):
    resp = client.get("/api/customers/999999")
    assert resp.status_code == 404


def test_persona_leaderboard_is_sorted_and_filtered(client):
    resp = client.get("/api/personas/explorer/leaderboard?limit=5")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) <= 5
    scores = [entry["score"] for entry in body]
    assert scores == sorted(scores, reverse=True)


def test_unknown_persona_leaderboard_is_404(client):
    resp = client.get("/api/personas/not-a-real-persona/leaderboard")
    assert resp.status_code == 404


def test_admin_recompute_rewrites_scores(client):
    n_customers = len(client.get("/api/customers?page_size=100").json())
    resp = client.post("/api/admin/recompute")
    assert resp.status_code == 200
    body = resp.json()
    # only true if n_customers <= 100 (page_size cap); fine for this dataset size
    assert body["persona_scores_written"] >= n_customers * len(PERSONAS)
