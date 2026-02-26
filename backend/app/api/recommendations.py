from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.recommendation import RecommendationList

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("", response_model=RecommendationList)
async def list_recommendations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ticker: str | None = Query(None, description="Filter by ticker symbol"),
    type: str | None = Query(None, description="Filter by BUY/HOLD/SELL"),
    db: AsyncSession = Depends(get_db),
) -> RecommendationList:
    """List recent recommendations with pagination."""
    # TODO Phase 3: query recommendations from DB
    return RecommendationList(items=[], total=0, page=page, page_size=page_size)
