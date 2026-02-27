"""
Ingestion service – Phase 2 implementation.
Handles RSS feed and YouTube channel fetching and persists new episodes to the DB.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime
from urllib.parse import parse_qs, urlparse

import feedparser
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.creator import Creator
from app.models.episode import Episode

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data container returned by the feed/channel fetchers
# ---------------------------------------------------------------------------

@dataclass
class EpisodeData:
    title: str
    source_url: str
    publish_date: date | None


# ---------------------------------------------------------------------------
# RSS
# ---------------------------------------------------------------------------

async def fetch_rss_feed(rss_url: str) -> list[EpisodeData]:
    """Fetch and parse episodes from an RSS feed URL.

    Runs feedparser in a thread-pool executor to avoid blocking the event loop.
    Returns episodes sorted newest-first.
    """
    import asyncio

    loop = asyncio.get_event_loop()
    feed = await loop.run_in_executor(None, feedparser.parse, rss_url)

    if feed.bozo and not feed.entries:
        logger.warning("RSS feed parse error for %s: %s", rss_url, feed.bozo_exception)
        return []

    episodes: list[EpisodeData] = []
    for entry in feed.entries:
        link = entry.get("link") or entry.get("id", "")
        if not link:
            continue

        pub_date: date | None = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                pub_date = date(*entry.published_parsed[:3])
            except (TypeError, ValueError):
                pass

        episodes.append(EpisodeData(
            title=entry.get("title", "Untitled"),
            source_url=link,
            publish_date=pub_date,
        ))

    return episodes


# ---------------------------------------------------------------------------
# YouTube Data API v3
# ---------------------------------------------------------------------------

_YT_API_BASE = "https://www.googleapis.com/youtube/v3"
_YT_PAGE_SIZE = 50  # hard limit per page


async def fetch_youtube_channel(channel_id: str, api_key: str = "") -> list[EpisodeData]:
    """Fetch recent videos from a YouTube channel via the Data API v3.

    Returns up to 100 episodes (2 pages) sorted newest-first.
    """
    episodes: list[EpisodeData] = []
    page_token: str | None = None
    pages_fetched = 0

    async with httpx.AsyncClient(timeout=15.0) as client:
        while pages_fetched < 2:
            params: dict[str, str | int] = {
                "part": "snippet",
                "channelId": channel_id,
                "type": "video",
                "order": "date",
                "maxResults": _YT_PAGE_SIZE,
                "key": api_key,
            }
            if page_token:
                params["pageToken"] = page_token

            try:
                resp = await client.get(f"{_YT_API_BASE}/search", params=params)
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                logger.error("YouTube API error for channel %s: %s", channel_id, exc)
                break

            data = resp.json()
            for item in data.get("items", []):
                video_id = item.get("id", {}).get("videoId")
                if not video_id:
                    continue
                snippet = item.get("snippet", {})
                pub_date: date | None = None
                if published_at := snippet.get("publishedAt"):
                    try:
                        pub_date = datetime.fromisoformat(
                            published_at.replace("Z", "+00:00")
                        ).date()
                    except ValueError:
                        pass

                episodes.append(EpisodeData(
                    title=snippet.get("title", "Untitled"),
                    source_url=f"https://www.youtube.com/watch?v={video_id}",
                    publish_date=pub_date,
                ))

            page_token = data.get("nextPageToken")
            pages_fetched += 1
            if not page_token:
                break

    return episodes


# ---------------------------------------------------------------------------
# YouTube URL helpers
# ---------------------------------------------------------------------------

def extract_youtube_video_id(url: str) -> str | None:
    """Return the YouTube video ID from a watch URL or youtu.be short link."""
    parsed = urlparse(url)
    if parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        ids = parse_qs(parsed.query).get("v")
        return ids[0] if ids else None
    if parsed.hostname == "youtu.be":
        return parsed.path.lstrip("/") or None
    return None


# ---------------------------------------------------------------------------
# DB persistence
# ---------------------------------------------------------------------------

async def ingest_episodes_for_creator(
    creator: Creator,
    db: AsyncSession,
    youtube_api_key: str = "",
) -> list[Episode]:
    """Fetch new episodes for *creator* and persist unseen ones to the DB.

    Returns the list of newly inserted Episode objects.  The caller is
    responsible for the surrounding transaction / commit.
    """
    if creator.platform == "youtube" and creator.youtube_channel_id:
        if not youtube_api_key:
            logger.warning("No YouTube API key – skipping creator '%s'", creator.name)
            return []
        raw_episodes = await fetch_youtube_channel(
            creator.youtube_channel_id, youtube_api_key
        )
    elif creator.rss_url:
        raw_episodes = await fetch_rss_feed(creator.rss_url)
    else:
        logger.warning("Creator '%s' has no rss_url or youtube_channel_id", creator.name)
        return []

    if not raw_episodes:
        return []

    # Avoid duplicates by loading known source URLs for this creator
    result = await db.execute(
        select(Episode.source_url).where(Episode.creator_id == creator.id)
    )
    known_urls: set[str] = {row[0] for row in result.all() if row[0]}

    new_episodes: list[Episode] = []
    for ep_data in raw_episodes:
        if ep_data.source_url in known_urls:
            continue
        episode = Episode(
            creator_id=creator.id,
            title=ep_data.title,
            source_url=ep_data.source_url,
            publish_date=ep_data.publish_date,
            processed=False,
        )
        db.add(episode)
        new_episodes.append(episode)

    if new_episodes:
        await db.flush()  # assign DB-generated IDs
        logger.info(
            "Ingested %d new episode(s) for creator '%s'",
            len(new_episodes),
            creator.name,
        )

    return new_episodes
