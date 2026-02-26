"""Integration tests for the ingestion pipeline – Phase 2."""
import pytest


@pytest.mark.asyncio
async def test_fetch_rss_feed_not_implemented():
    from app.services.ingestion import fetch_rss_feed

    with pytest.raises(NotImplementedError):
        await fetch_rss_feed("https://example.com/feed.xml")


@pytest.mark.asyncio
async def test_fetch_youtube_channel_not_implemented():
    from app.services.ingestion import fetch_youtube_channel

    with pytest.raises(NotImplementedError):
        await fetch_youtube_channel("UCxxx")
