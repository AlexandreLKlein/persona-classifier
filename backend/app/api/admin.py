from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.database import get_session
from app.schemas import RecomputeResultOut
from app.scoring import recompute_all_scores

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/recompute", response_model=RecomputeResultOut)
def recompute(session: Session = Depends(get_session)) -> RecomputeResultOut:
    """Re-runs the feature engineering + scoring pipeline against current data.

    Mirrors the real system's nightly batch job, exposed synchronously here for the demo.
    """
    count = recompute_all_scores(session)
    return RecomputeResultOut(persona_scores_written=count)
