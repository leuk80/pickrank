"""
NLP extraction service – Phase 2 implementation.
Detects tickers/companies and classifies recommendation type via OpenAI.
Confidence threshold: > 0.7 (discard below).
Target false-positive rate: < 20%.
"""
from typing import Any


async def extract_recommendations(transcript: str) -> list[dict[str, Any]]:
    """Extract BUY/HOLD/SELL recommendations from a transcript."""
    raise NotImplementedError("Implemented in Phase 2")
