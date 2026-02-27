"""
NLP extraction service – Phase 2 implementation.

Pipeline:
1. Regex  → finds potential ticker patterns (1–5 uppercase letters) as hints.
2. OpenAI → receives full transcript + ticker hints, returns structured
            BUY/HOLD/SELL recommendations with confidence scores.
3. Filter → discard recommendations with confidence ≤ 0.7.

Note: spaCy was intentionally removed – its heavy dependencies (numpy, thinc,
blis, …) push the Vercel bundle over the 250 MB limit.  OpenAI gpt-4o-mini
handles company-name and ticker resolution reliably without NER hints.

Target false-positive rate: < 20%.
"""
from __future__ import annotations

import json
import logging
import re
import textwrap
from typing import Any

logger = logging.getLogger(__name__)

# Confidence threshold defined in CLAUDE.md
_CONFIDENCE_THRESHOLD = 0.7

# Regex: 1–5 uppercase letters that look like a ticker symbol.
# Excludes very common English/German words that happen to be all-caps.
_TICKER_REGEX = re.compile(r"\b[A-Z]{1,5}\b")
_COMMON_WORDS: frozenset[str] = frozenset({
    "I", "A", "AN", "THE", "AND", "OR", "BUT", "IN", "ON", "AT", "TO",
    "FOR", "OF", "AS", "BY", "FROM", "WITH", "IS", "ARE", "WAS", "BE",
    "IT", "ITS", "IF", "NOT", "NO", "SO", "DO", "GO", "WE", "US", "HE",
    "SHE", "HIS", "HER", "THAT", "THIS", "CEO", "CFO", "COO", "IPO",
    "ETF", "GDP", "CPI", "FED", "ECB", "ESG", "AI", "IT", "API", "Q1",
    "Q2", "Q3", "Q4", "YOY", "QOQ", "PE", "EPS", "DCF", "FCF",
})

# Maximum transcript characters sent to OpenAI (≈ 80k tokens with gpt-4o-mini)
_MAX_TRANSCRIPT_CHARS = 120_000

# OpenAI model – gpt-4o-mini balances cost and quality for extraction tasks
_OPENAI_MODEL = "gpt-4o-mini"

_SYSTEM_PROMPT = textwrap.dedent("""
    You are a financial analyst assistant that extracts stock recommendations
    from investment podcast and YouTube video transcripts.

    Your task: identify every explicit stock recommendation (BUY, HOLD, or SELL)
    mentioned in the transcript.  Return ONLY a JSON object with this structure:

    {
      "recommendations": [
        {
          "ticker": "AAPL",
          "company_name": "Apple Inc.",
          "type": "BUY",
          "confidence": 0.92,
          "sentence": "I think Apple is a clear buy at these levels."
        }
      ]
    }

    Rules:
    - Include only explicit recommendations – ignore vague mentions.
    - Ticker must be the standard exchange symbol (e.g. AAPL, SAP, BMW).
      If you cannot determine the ticker with confidence, use the most likely
      exchange symbol based on context (XETRA for German stocks, NYSE/NASDAQ
      for US stocks).
    - "type" must be exactly "BUY", "HOLD", or "SELL".
    - "confidence" is a float 0.0–1.0 reflecting how certain you are that
      this is an actual recommendation (not just a mention or analysis).
    - "sentence" is the verbatim sentence(s) from the transcript that contain
      the recommendation.
    - If no recommendations are found, return {"recommendations": []}.
    - Do NOT add explanations outside the JSON object.
""").strip()


def _extract_ticker_candidates(text: str) -> list[str]:
    """Return potential ticker symbols found via regex, filtered for noise."""
    matches = _TICKER_REGEX.findall(text)
    seen: set[str] = set()
    tickers: list[str] = []
    for m in matches:
        if m not in _COMMON_WORDS and m not in seen:
            seen.add(m)
            tickers.append(m)
    return tickers


# ---------------------------------------------------------------------------
# OpenAI extraction
# ---------------------------------------------------------------------------

def _mock_recommendations(transcript: str) -> list[dict[str, Any]]:
    """Return deterministic stub data without calling OpenAI.

    Activated when the environment variable OPENAI_MOCK=true is set.
    Returns two fake recommendations so the full DB-write path can be tested.
    """
    # Pick a word from the transcript to make the stub feel dynamic
    words = [w for w in transcript.split() if w.isupper() and 2 <= len(w) <= 5]
    ticker = words[0] if words else "TEST"
    return [
        {
            "ticker": ticker,
            "company_name": f"{ticker} Corp. (mock)",
            "type": "BUY",
            "confidence": 0.99,
            "sentence": f"[MOCK] Extracted from transcript — OpenAI is disabled (OPENAI_MOCK=true).",
        },
        {
            "ticker": "MOCK",
            "company_name": "Mock Holdings AG",
            "type": "HOLD",
            "confidence": 0.85,
            "sentence": "[MOCK] Second stub recommendation for pipeline testing.",
        },
    ]


async def _call_openai(transcript: str, ticker_hints: list[str]) -> list[dict[str, Any]]:
    """Send the transcript to OpenAI and parse the structured response.

    Returns a list of raw recommendation dicts (not yet confidence-filtered).
    """
    from openai import AsyncOpenAI

    client = AsyncOpenAI()

    # Truncate very long transcripts to stay within context limits
    truncated = transcript[:_MAX_TRANSCRIPT_CHARS]
    if len(transcript) > _MAX_TRANSCRIPT_CHARS:
        logger.info(
            "Transcript truncated from %d to %d chars for OpenAI",
            len(transcript),
            _MAX_TRANSCRIPT_CHARS,
        )

    hint = ""
    if ticker_hints:
        sample = ", ".join(ticker_hints[:30])
        hint = f"\n\nPotential ticker symbols found in transcript: {sample}"

    user_message = f"Extract all stock recommendations from this transcript:{hint}\n\n---\n{truncated}\n---"

    try:
        response = await client.chat.completions.create(
            model=_OPENAI_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0,
        )
    except Exception as exc:
        logger.error("OpenAI API call failed: %s", exc)
        return []

    raw_content = response.choices[0].message.content or "{}"
    try:
        parsed = json.loads(raw_content)
        return parsed.get("recommendations", [])
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse OpenAI response as JSON: %s\n%s", exc, raw_content[:500])
        return []


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def extract_recommendations(transcript: str) -> list[dict[str, Any]]:
    """Extract BUY/HOLD/SELL recommendations from a transcript.

    Returns a list of dicts with keys:
        ticker, company_name, type, confidence, sentence

    Recommendations with confidence ≤ 0.7 are discarded.

    Set OPENAI_MOCK=true to skip the OpenAI call and return stub data instead.
    """
    import os

    if not transcript or not transcript.strip():
        return []

    # 1. Regex ticker hints (lightweight, no heavy dependencies)
    ticker_hints = _extract_ticker_candidates(transcript)
    logger.debug("Regex ticker candidates: %s", ticker_hints[:10])

    # 2. OpenAI classification (or mock stub)
    if os.getenv("OPENAI_MOCK", "").lower() in ("1", "true", "yes"):
        logger.warning("OPENAI_MOCK is enabled – returning stub recommendations, no API call made.")
        raw_recs = _mock_recommendations(transcript)
    else:
        raw_recs = await _call_openai(transcript, ticker_hints)
    logger.info("OpenAI returned %d raw recommendation(s)", len(raw_recs))

    # 3. Validate and filter by confidence threshold
    results: list[dict[str, Any]] = []
    for rec in raw_recs:
        ticker = str(rec.get("ticker", "")).strip().upper()
        rec_type = str(rec.get("type", "")).strip().upper()
        confidence = float(rec.get("confidence", 0.0))

        if not ticker or rec_type not in ("BUY", "HOLD", "SELL"):
            logger.debug("Skipping invalid recommendation: %s", rec)
            continue

        if confidence <= _CONFIDENCE_THRESHOLD:
            logger.debug(
                "Discarding low-confidence recommendation %s %s (%.2f)",
                rec_type, ticker, confidence,
            )
            continue

        results.append({
            "ticker": ticker,
            "company_name": rec.get("company_name") or None,
            "type": rec_type,
            "confidence": confidence,
            "sentence": rec.get("sentence") or None,
        })

    logger.info(
        "%d recommendation(s) passed confidence filter (threshold=%.2f)",
        len(results),
        _CONFIDENCE_THRESHOLD,
    )
    return results
