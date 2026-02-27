"""Unit tests for NLP extraction (Phase 2)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.nlp_extraction import (
    _CONFIDENCE_THRESHOLD,
    _extract_ticker_candidates,
    extract_recommendations,
)


# ---------------------------------------------------------------------------
# Ticker regex helper
# ---------------------------------------------------------------------------

def test_extract_ticker_candidates_finds_symbols() -> None:
    text = "I think AAPL and MSFT are great buys. The CEO said so."
    tickers = _extract_ticker_candidates(text)
    assert "AAPL" in tickers
    assert "MSFT" in tickers
    # Common words must be filtered out
    assert "CEO" not in tickers
    assert "THE" not in tickers
    assert "I" not in tickers


def test_extract_ticker_candidates_deduplicates() -> None:
    text = "AAPL is up. AAPL looks good. AAPL again."
    tickers = _extract_ticker_candidates(text)
    assert tickers.count("AAPL") == 1


# ---------------------------------------------------------------------------
# extract_recommendations – OpenAI mocked
# ---------------------------------------------------------------------------

def _make_openai_response(recs: list[dict]) -> MagicMock:
    """Build a minimal mock of an OpenAI chat completion response."""
    import json

    content = json.dumps({"recommendations": recs})
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


@pytest.mark.asyncio
async def test_extract_recommendations_returns_high_confidence() -> None:
    openai_recs = [
        {
            "ticker": "AAPL",
            "company_name": "Apple Inc.",
            "type": "BUY",
            "confidence": 0.95,
            "sentence": "Apple is a clear buy.",
        },
    ]

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=_make_openai_response(openai_recs)
    )

    with (
        patch("app.services.nlp_extraction.AsyncOpenAI", return_value=mock_client),
        patch("app.services.nlp_extraction._get_nlp", return_value=None),
    ):
        results = await extract_recommendations("Apple is a clear buy at these levels.")

    assert len(results) == 1
    assert results[0]["ticker"] == "AAPL"
    assert results[0]["type"] == "BUY"
    assert results[0]["confidence"] == 0.95


@pytest.mark.asyncio
async def test_extract_recommendations_filters_low_confidence() -> None:
    openai_recs = [
        {"ticker": "TSLA", "company_name": "Tesla", "type": "BUY", "confidence": 0.5, "sentence": "Maybe Tesla."},
        {"ticker": "NVDA", "company_name": "Nvidia", "type": "SELL", "confidence": 0.85, "sentence": "Sell Nvidia."},
    ]

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=_make_openai_response(openai_recs)
    )

    with (
        patch("app.services.nlp_extraction.AsyncOpenAI", return_value=mock_client),
        patch("app.services.nlp_extraction._get_nlp", return_value=None),
    ):
        results = await extract_recommendations("Maybe Tesla. Definitely sell Nvidia.")

    assert len(results) == 1
    assert results[0]["ticker"] == "NVDA"


@pytest.mark.asyncio
async def test_extract_recommendations_empty_transcript_returns_empty() -> None:
    results = await extract_recommendations("")
    assert results == []


@pytest.mark.asyncio
async def test_extract_recommendations_openai_error_returns_empty() -> None:
    from openai import APIError

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=Exception("OpenAI API error")
    )

    with (
        patch("app.services.nlp_extraction.AsyncOpenAI", return_value=mock_client),
        patch("app.services.nlp_extraction._get_nlp", return_value=None),
    ):
        results = await extract_recommendations("Some transcript text.")

    assert results == []


@pytest.mark.asyncio
async def test_extract_recommendations_invalid_type_discarded() -> None:
    openai_recs = [
        {"ticker": "BMW", "company_name": "BMW AG", "type": "STRONG_BUY", "confidence": 0.9, "sentence": "Strong buy BMW."},
        {"ticker": "SAP", "company_name": "SAP SE", "type": "BUY", "confidence": 0.88, "sentence": "Buy SAP."},
    ]

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=_make_openai_response(openai_recs)
    )

    with (
        patch("app.services.nlp_extraction.AsyncOpenAI", return_value=mock_client),
        patch("app.services.nlp_extraction._get_nlp", return_value=None),
    ):
        results = await extract_recommendations("Strong buy BMW. Buy SAP.")

    assert len(results) == 1
    assert results[0]["ticker"] == "SAP"
