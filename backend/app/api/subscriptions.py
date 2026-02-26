from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.subscription import SubscriptionCreate, SubscriptionResponse

router = APIRouter(prefix="/subscribe", tags=["subscriptions"])


@router.post("", response_model=SubscriptionResponse, status_code=201)
async def subscribe(
    payload: SubscriptionCreate,
    db: AsyncSession = Depends(get_db),
) -> SubscriptionResponse:
    """Subscribe an email address to creator performance alerts."""
    # TODO Phase 5: persist subscription, trigger SendGrid confirmation email
    return SubscriptionResponse(
        message="Subscription erfolgreich. Sie erhalten bald eine Bestätigungs-E-Mail.",
        email=payload.email,
    )
