"""
Scheduled background jobs – Phase 2 implementation.
Ingestion cycle: fetch → transcribe → NLP extract → persist.
Runs every 6 hours (configured externally via Celery beat or APScheduler).
"""
from __future__ import annotations

import logging
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models.creator import Creator
from app.models.episode import Episode
from app.models.recommendation import Recommendation
from app.services.ingestion import ingest_episodes_for_creator
from app.services.nlp_extraction import extract_recommendations
from app.services.transcription import get_transcript

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Per-episode processing
# ---------------------------------------------------------------------------

async def process_episode(episode: Episode, db: AsyncSession) -> int:
    """Transcribe and run NLP on a single unprocessed episode.

    Marks the episode as processed regardless of outcome (to avoid retrying
    broken episodes indefinitely).  Returns the number of recommendations saved.
    """
    logger.info("Processing episode '%s' (%s)", episode.title, episode.source_url)

    # Determine preferred language from the creator (loaded via relationship)
    language = "de"
    if episode.creator and episode.creator.language:
        language = episode.creator.language

    # 1. Get transcript
    transcript: str | None = None
    if episode.transcript:
        transcript = episode.transcript  # already stored (e.g. manual upload)
    elif episode.source_url:
        transcript = await get_transcript(episode.source_url, language=language)

    if not transcript:
        logger.warning("No transcript available for episode %s – skipping NLP", episode.id)
        episode.processed = True
        return 0

    # Store transcript on the episode for future reference
    episode.transcript = transcript

    # 2. NLP extraction
    raw_recs = await extract_recommendations(transcript)

    # 3. Persist recommendations
    saved = 0
    for rec_data in raw_recs:
        recommendation = Recommendation(
            episode_id=episode.id,
            ticker=rec_data["ticker"],
            company_name=rec_data.get("company_name"),
            type=rec_data["type"],
            confidence=rec_data.get("confidence"),
            sentence=rec_data.get("sentence"),
            recommendation_date=episode.publish_date or date.today(),
        )
        db.add(recommendation)
        saved += 1

    episode.processed = True
    logger.info(
        "Episode '%s': saved %d recommendation(s)", episode.title, saved
    )
    return saved


# ---------------------------------------------------------------------------
# Full ingestion cycle
# ---------------------------------------------------------------------------

async def run_ingestion_cycle() -> dict[str, int]:
    """Full ingestion cycle (Phase 2 scope):

    1. Load all creators from DB.
    2. For each creator: fetch new episodes via RSS / YouTube API.
    3. For each new episode: get transcript + run NLP + save recommendations.
    4. Commit after each creator to limit transaction scope.

    Returns a summary dict with counts for monitoring.
    """
    settings = get_settings()
    total_new_episodes = 0
    total_recommendations = 0
    total_creators = 0

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Creator))
        creators: list[Creator] = list(result.scalars().all())

    logger.info("Starting ingestion cycle for %d creator(s)", len(creators))

    for creator in creators:
        try:
            async with AsyncSessionLocal() as db:
                # Re-attach creator to this session
                creator_in_session = await db.get(Creator, creator.id)
                if creator_in_session is None:
                    continue

                # 1. Fetch & persist new episodes
                new_episodes = await ingest_episodes_for_creator(
                    creator_in_session,
                    db,
                    youtube_api_key=settings.youtube_api_key,
                )
                total_new_episodes += len(new_episodes)

                # 2. Also process any previously fetched but unprocessed episodes
                unprocessed_result = await db.execute(
                    select(Episode).where(
                        Episode.creator_id == creator.id,
                        Episode.processed.is_(False),
                    )
                )
                unprocessed = list(unprocessed_result.scalars().all())

                # Eager-load creator on episodes for language detection
                for ep in unprocessed:
                    ep.creator = creator_in_session

                # 3. Process each unprocessed episode
                for episode in unprocessed:
                    recs_saved = await process_episode(episode, db)
                    total_recommendations += recs_saved

                await db.commit()
                total_creators += 1

        except Exception as exc:
            logger.error(
                "Error during ingestion for creator '%s': %s",
                creator.name,
                exc,
                exc_info=True,
            )
            # Continue with next creator – don't abort the full cycle

    summary = {
        "creators_processed": total_creators,
        "new_episodes": total_new_episodes,
        "recommendations_saved": total_recommendations,
    }
    logger.info("Ingestion cycle complete: %s", summary)
    return summary
