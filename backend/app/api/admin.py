"""
Admin API – Phase 2 test interface endpoints.
Protected by X-Admin-Key header (set ADMIN_API_KEY in .env / Vercel env vars).

Designed for Vercel serverless: each endpoint completes well within 60 s.

Endpoints:
  POST   /api/admin/creators                     – create a creator
  GET    /api/admin/creators                     – list creators with counts
  POST   /api/admin/fetch/{creator_id}           – fetch episode metadata only (fast, < 5 s)
  POST   /api/admin/process/{episode_id}         – transcript + NLP for ONE episode (< 60 s)
  GET    /api/admin/episodes/{creator_id}        – list episodes for a creator
  GET    /api/admin/recommendations/{episode_id} – list recs for an episode
"""
from __future__ import annotations

import uuid
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.creator import Creator
from app.models.episode import Episode
from app.models.recommendation import Recommendation
from app.services.ingestion import ingest_episodes_for_creator
from app.tasks.cron import process_episode

router = APIRouter(prefix="/admin", tags=["admin"])


# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------

def require_admin(x_admin_key: str | None = Header(None, alias="X-Admin-Key")) -> None:
    settings = get_settings()
    if not settings.admin_api_key or x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Admin-Key header")


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class CreatorCreateRequest(BaseModel):
    name: str
    platform: Literal["youtube", "podcast"]
    language: Literal["de", "en"] = "de"
    rss_url: str | None = None
    youtube_channel_id: str | None = None


class AdminCreatorRead(BaseModel):
    id: uuid.UUID
    name: str
    platform: str
    language: str
    rss_url: str | None
    youtube_channel_id: str | None
    episode_count: int
    recommendation_count: int
    unprocessed_count: int

    model_config = {"from_attributes": True}


class FetchResult(BaseModel):
    creator_id: uuid.UUID
    creator_name: str
    new_episodes: int
    error: str | None = None


class ProcessResult(BaseModel):
    episode_id: uuid.UUID
    episode_title: str
    recommendations_saved: int
    error: str | None = None


class AdminEpisodeRead(BaseModel):
    id: uuid.UUID
    title: str
    source_url: str | None
    publish_date: date | None
    processed: bool
    recommendation_count: int


class AdminRecommendationRead(BaseModel):
    id: uuid.UUID
    ticker: str
    company_name: str | None
    type: str
    confidence: float | None
    sentence: str | None
    recommendation_date: date | None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/creators",
    response_model=AdminCreatorRead,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
async def create_creator(
    payload: CreatorCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> AdminCreatorRead:
    """Add a new creator to the system."""
    if not payload.rss_url and not payload.youtube_channel_id:
        raise HTTPException(
            status_code=422,
            detail="Either rss_url or youtube_channel_id is required.",
        )

    creator = Creator(
        name=payload.name,
        platform=payload.platform,
        language=payload.language,
        rss_url=payload.rss_url,
        youtube_channel_id=payload.youtube_channel_id,
    )
    db.add(creator)
    await db.flush()

    return AdminCreatorRead(
        id=creator.id,
        name=creator.name,
        platform=creator.platform,
        language=creator.language,
        rss_url=creator.rss_url,
        youtube_channel_id=creator.youtube_channel_id,
        episode_count=0,
        recommendation_count=0,
        unprocessed_count=0,
    )


@router.get(
    "/creators",
    response_model=list[AdminCreatorRead],
    dependencies=[Depends(require_admin)],
)
async def list_creators(
    db: AsyncSession = Depends(get_db),
) -> list[AdminCreatorRead]:
    """List all creators with episode and recommendation counts."""
    result = await db.execute(select(Creator).order_by(Creator.created_at.desc()))
    creators = list(result.scalars().all())

    output: list[AdminCreatorRead] = []
    for c in creators:
        ep_count: int = (
            await db.execute(select(func.count()).where(Episode.creator_id == c.id))
        ).scalar_one()

        unprocessed: int = (
            await db.execute(
                select(func.count()).where(
                    Episode.creator_id == c.id,
                    Episode.processed.is_(False),
                )
            )
        ).scalar_one()

        rec_count: int = (
            await db.execute(
                select(func.count(Recommendation.id))
                .join(Episode, Recommendation.episode_id == Episode.id)
                .where(Episode.creator_id == c.id)
            )
        ).scalar_one()

        output.append(AdminCreatorRead(
            id=c.id,
            name=c.name,
            platform=c.platform,
            language=c.language,
            rss_url=c.rss_url,
            youtube_channel_id=c.youtube_channel_id,
            episode_count=ep_count,
            recommendation_count=rec_count,
            unprocessed_count=unprocessed,
        ))

    return output


@router.post(
    "/fetch/{creator_id}",
    response_model=FetchResult,
    dependencies=[Depends(require_admin)],
)
async def fetch_episodes(
    creator_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> FetchResult:
    """Fetch episode metadata from YouTube/RSS and save to DB.

    Fast endpoint (< 5 s): only retrieves titles, dates, URLs — no transcripts,
    no OpenAI.  Safe to call on Vercel free plan.
    """
    settings = get_settings()

    creator = await db.get(Creator, creator_id)
    if creator is None:
        raise HTTPException(status_code=404, detail="Creator not found")

    try:
        new_episodes = await ingest_episodes_for_creator(
            creator, db, youtube_api_key=settings.youtube_api_key
        )
        await db.commit()
        return FetchResult(
            creator_id=creator_id,
            creator_name=creator.name,
            new_episodes=len(new_episodes),
        )
    except Exception as exc:
        return FetchResult(
            creator_id=creator_id,
            creator_name=creator.name,
            new_episodes=0,
            error=str(exc),
        )


@router.post(
    "/process/{episode_id}",
    response_model=ProcessResult,
    dependencies=[Depends(require_admin)],
)
async def process_one_episode(
    episode_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ProcessResult:
    """Transcribe and run NLP extraction for a single episode.

    Slow endpoint (~10–40 s): calls youtube-transcript-api + OpenAI.
    Processes exactly one episode — call once per episode from the frontend.
    Requires Vercel Pro plan (maxDuration: 60) or run locally.
    """
    episode = await db.get(Episode, episode_id)
    if episode is None:
        raise HTTPException(status_code=404, detail="Episode not found")

    # Load creator for language detection
    creator = await db.get(Creator, episode.creator_id)
    if creator:
        episode.creator = creator

    try:
        recs_saved = await process_episode(episode, db)
        await db.commit()
        return ProcessResult(
            episode_id=episode_id,
            episode_title=episode.title,
            recommendations_saved=recs_saved,
        )
    except Exception as exc:
        return ProcessResult(
            episode_id=episode_id,
            episode_title=episode.title,
            recommendations_saved=0,
            error=str(exc),
        )


@router.get(
    "/episodes/{creator_id}",
    response_model=list[AdminEpisodeRead],
    dependencies=[Depends(require_admin)],
)
async def list_episodes(
    creator_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[AdminEpisodeRead]:
    """List episodes for a creator, newest first."""
    result = await db.execute(
        select(Episode)
        .where(Episode.creator_id == creator_id)
        .order_by(Episode.publish_date.desc().nulls_last(), Episode.created_at.desc())
    )
    episodes = list(result.scalars().all())

    output: list[AdminEpisodeRead] = []
    for ep in episodes:
        rec_count: int = (
            await db.execute(
                select(func.count()).where(Recommendation.episode_id == ep.id)
            )
        ).scalar_one()

        output.append(AdminEpisodeRead(
            id=ep.id,
            title=ep.title,
            source_url=ep.source_url,
            publish_date=ep.publish_date,
            processed=ep.processed,
            recommendation_count=rec_count,
        ))

    return output


@router.get(
    "/recommendations/{episode_id}",
    response_model=list[AdminRecommendationRead],
    dependencies=[Depends(require_admin)],
)
async def list_recommendations(
    episode_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[AdminRecommendationRead]:
    """List all extracted recommendations for an episode."""
    result = await db.execute(
        select(Recommendation)
        .where(Recommendation.episode_id == episode_id)
        .order_by(Recommendation.confidence.desc().nulls_last())
    )
    recs = list(result.scalars().all())

    return [
        AdminRecommendationRead(
            id=r.id,
            ticker=r.ticker,
            company_name=r.company_name,
            type=r.type,
            confidence=r.confidence,
            sentence=r.sentence,
            recommendation_date=r.recommendation_date,
        )
        for r in recs
    ]
