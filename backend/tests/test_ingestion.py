"""Tests for the ingestion service (Phase 2)."""
from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ingestion import (
    EpisodeData,
    extract_youtube_video_id,
    fetch_rss_feed,
    fetch_youtube_channel,
)


# ---------------------------------------------------------------------------
# extract_youtube_video_id
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("url,expected", [
    ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ("https://m.youtube.com/watch?v=abc123", "abc123"),
    ("https://example.com/podcast.mp3", None),
    ("", None),
])
def test_extract_youtube_video_id(url: str, expected: str | None) -> None:
    assert extract_youtube_video_id(url) == expected


# ---------------------------------------------------------------------------
# fetch_rss_feed
# ---------------------------------------------------------------------------

def _make_rss_entry(title: str, link: str, published_parsed: tuple) -> MagicMock:
    entry = MagicMock()
    entry.get.side_effect = lambda k, default="": {"title": title, "link": link}.get(k, default)
    entry.published_parsed = published_parsed
    return entry


@pytest.mark.asyncio
async def test_fetch_rss_feed_returns_episodes() -> None:
    mock_feed = MagicMock(bozo=False)
    mock_feed.entries = [
        _make_rss_entry("Episode 1", "https://podcast.example.com/ep1", (2024, 3, 15, 0, 0, 0, 0, 0, 0)),
        _make_rss_entry("Episode 2", "https://podcast.example.com/ep2", (2024, 3, 8, 0, 0, 0, 0, 0, 0)),
    ]

    with patch("app.services.ingestion.feedparser.parse", return_value=mock_feed):
        episodes = await fetch_rss_feed("https://podcast.example.com/feed.xml")

    assert len(episodes) == 2
    assert all(isinstance(ep, EpisodeData) for ep in episodes)
    assert episodes[0].source_url == "https://podcast.example.com/ep1"
    assert episodes[0].publish_date == date(2024, 3, 15)
    assert episodes[1].title == "Episode 2"


@pytest.mark.asyncio
async def test_fetch_rss_feed_bozo_empty_returns_empty() -> None:
    mock_feed = MagicMock(bozo=True, bozo_exception=Exception("bad xml"), entries=[])
    with patch("app.services.ingestion.feedparser.parse", return_value=mock_feed):
        episodes = await fetch_rss_feed("https://broken.example.com/feed.xml")

    assert episodes == []


# ---------------------------------------------------------------------------
# fetch_youtube_channel
# ---------------------------------------------------------------------------

_FAKE_YT_RESPONSE = {
    "items": [
        {
            "id": {"videoId": "vid001"},
            "snippet": {"title": "Stock Pick Video", "publishedAt": "2024-03-20T10:00:00Z"},
        },
        {
            "id": {"videoId": "vid002"},
            "snippet": {"title": "Market Update", "publishedAt": "2024-03-13T10:00:00Z"},
        },
    ],
}


@pytest.mark.asyncio
async def test_fetch_youtube_channel_returns_episodes() -> None:
    mock_resp = MagicMock()
    mock_resp.json.return_value = _FAKE_YT_RESPONSE
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.ingestion.httpx.AsyncClient", return_value=mock_client):
        episodes = await fetch_youtube_channel("UCtest123", api_key="fake-key")

    assert len(episodes) == 2
    assert episodes[0].source_url == "https://www.youtube.com/watch?v=vid001"
    assert episodes[0].title == "Stock Pick Video"
    assert episodes[0].publish_date == date(2024, 3, 20)


@pytest.mark.asyncio
async def test_fetch_youtube_channel_http_error_returns_empty() -> None:
    import httpx

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(side_effect=httpx.RequestError("connection refused"))

    with patch("app.services.ingestion.httpx.AsyncClient", return_value=mock_client):
        episodes = await fetch_youtube_channel("UCtest123", api_key="fake-key")

    assert episodes == []
