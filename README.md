# 🍺 Persona Classifier

_Live demo: not yet deployed -- see [Deployment](#deployment) below._

A from-scratch, synthetic-data reimplementation of a nightly customer-scoring job I
built for a real taproom's POS system, rebuilt standalone in Python + Vue because the
original can't be open-sourced. Enter the app, browse a synthetic customer base of a
few hundred fictional taproom regulars, and see each one scored 0-100 against five
original behavioral personas -- with a fully transparent, explainable breakdown of
*why* each score landed where it did.

## Why this exists

The real system (part of a brewery/taproom ERP I built and maintain) runs a nightly
batch job that scores every customer against a set of behavioral personas -- useful for
staff to spot, at a glance, who's a high-frequency regular versus who mostly shows up
for events. That real job can't be open-sourced: its persona taxonomy and scoring
weights are the brewery's own business logic, and the data behind it is real customer
records.

This project rebuilds the *idea* from scratch and in the open: an original five-persona
taxonomy I designed independently (different names, different weights, no relationship
to the real system), scored against 100% synthetic, seed-generated data. Nothing here
is the brewery's proprietary logic, and no real customer ever appears in this repo.

**Why the personas here are safe to publish, unlike a public style guide:** a project
in the same portfolio ([`beer-style-classifier`](https://github.com/AlexandreLKlein/beer-style-classifier))
classifies beers against the BJCP style guidelines -- a public, published standard, so
reimplementing it isn't a confidentiality question. Customer personas have no public
standard to point to; the taxonomy below is original work, built independently for this
project, with a synthetic dataset generated specifically so no real business or
customer data is ever at risk.

## How scoring works

1. **Generate** a synthetic dataset (`app/data/generator.py`): ~150-300 fictional
   customers, each biased toward one of five persona archetypes (plus a noisy "mixed"
   long tail for realism), with 3-24 months of fabricated visit and purchase history.
2. **Engineer features** (`app/features.py`): pandas aggregates each customer's raw
   behavior -- recency, frequency, tenure, total spend, average ticket, style
   diversity, event-attendance ratio, spend consistency -- then min-max normalizes each
   into a 0-100 sub-score *relative to the current population* (there's no external
   ground truth for what "frequent" means for an arbitrary taproom).
3. **Score** (`app/scoring.py`): each of the five personas is a weighted combination of
   those sub-scores. The weights are public (`GET /api/personas`), and every score ships
   with a full per-feature contribution breakdown -- explainability is a first-class API
   feature, not an afterthought.

### The five personas

| Persona | What it captures | Primary signals |
|---|---|---|
| The Regular | Visits often and recently | recency, frequency, tenure |
| The Explorer | Tries a wide range of styles/categories | style diversity, event ratio, frequency |
| The Big Tab | Spends well above average | average ticket, total spend |
| The Event Chaser | Shows up mainly for ticketed events | event ratio, frequency |
| The Quiet Sipper | Long-tenured, infrequent, consistent | tenure, low frequency, spend consistency |

See `app/personas.py` for the exact weights.

## Architecture

```
Vue 3 + Vite + TS + Pinia SPA
  |-- GET  /api/customers?sort=&persona=&page=     leaderboard/table
  |-- GET  /api/customers/{id}                     detail: radar chart + score breakdown
  |-- GET  /api/personas                           rubric explainer (transparent weights)
  |-- GET  /api/personas/{key}/leaderboard
  |-- POST /api/admin/recompute                     re-run scoring pipeline on demand
  v
FastAPI + Pydantic v2
  |-- app/features.py     pandas groupby/agg -> recency/frequency/monetary/diversity
  |-- app/scoring.py      weighted-rubric scorer per PersonaDefinition
  |-- app/data/generator.py   Faker + numpy, seeded synthetic dataset
  v
SQLite via SQLModel, seeded automatically on first startup if empty
```

## Tech stack

| Layer | Choice |
|---|---|
| Backend framework | FastAPI + Pydantic v2 |
| Data / ML | pandas, numpy, scikit-learn (available for the similarity stretch goal) |
| Storage | SQLite via SQLModel -- no external DB service to provision |
| Synthetic data | Faker |
| Frontend | Vue 3 + Vite + TypeScript + Pinia + vue-router |
| Charts | Chart.js / vue-chartjs (radar chart) |
| Styling | Tailwind CSS v4 |
| Tests | pytest (backend), Vitest + @vue/test-utils (frontend) |
| Tooling | ruff (backend lint), ESLint + oxlint + Prettier (frontend), GitHub Actions CI, Docker |

## Getting started

Requires Python 3.12+ and Node.js 20.9+.

### Backend

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate       # or `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

The database seeds itself automatically on first startup (~200 synthetic customers).
API docs: http://localhost:8000/docs

To force a fresh dataset at any time: `python -m app.data.seed`

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Visit http://localhost:5173.

### Tests

```bash
cd backend && pytest -q
cd frontend && npx vitest run
```

## Deployment

Backend: any container host that can run the Dockerfile (e.g. Railway) -- no separate
database service is needed since SQLite seeds itself on container startup. Frontend:
any static host (Vercel, Netlify, Cloudflare Pages) pointed at the deployed backend via
`VITE_API_BASE_URL`. FastAPI's auto-generated `/docs` (Swagger UI) is worth linking
alongside the frontend demo -- the API is explorable on its own.

## License

MIT -- see [LICENSE](LICENSE).
