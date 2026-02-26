from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.ranking import RankingResponse

router = APIRouter(prefix="/ranking", tags=["ranking"])


@router.get("", response_model=RankingResponse)
async def get_ranking(
    limit: int = Query(50, ge=1, le=200),
    language: str | None = Query(None, description="Filter by language: de or en"),
    db: AsyncSession = Depends(get_db),
) -> RankingResponse:
    """Get creators ranked by overall_score. Requires minimum 20 picks."""
    # TODO Phase 3: query creator_scores ordered by overall_score desc, filter total_picks >= 20
    return RankingResponse(items=[], total=0)
