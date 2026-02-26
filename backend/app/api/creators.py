from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.creator import CreatorList, CreatorRead

router = APIRouter(prefix="/creators", tags=["creators"])


@router.get("", response_model=CreatorList)
async def list_creators(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> CreatorList:
    """List all creators with their scores."""
    # TODO Phase 3: query creators with score join
    return CreatorList(items=[], total=0)


@router.get("/{creator_id}", response_model=CreatorRead)
async def get_creator(
    creator_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> CreatorRead:
    """Get a single creator by ID with all their picks."""
    # TODO Phase 3: fetch creator and recommendations
    raise HTTPException(status_code=404, detail="Creator not found")
