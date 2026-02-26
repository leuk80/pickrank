"""
Ingestion service – Phase 2 implementation.
Handles RSS feed and YouTube channel fetching.
"""
from typing import Any


async def fetch_rss_feed(rss_url: str) -> list[dict[str, Any]]:
    """Fetch and parse episodes from an RSS feed URL."""
    raise NotImplementedError("Implemented in Phase 2")


async def fetch_youtube_channel(channel_id: str) -> list[dict[str, Any]]:
    """Fetch recent videos from a YouTube channel via the Data API."""
    raise NotImplementedError("Implemented in Phase 2")
