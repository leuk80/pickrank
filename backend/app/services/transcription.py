"""
Transcription service – Phase 2 implementation.
1. Tries to fetch an existing YouTube transcript (free, no API key needed).
2. Falls back to OpenAI Whisper for podcast audio files.
"""
from __future__ import annotations

import logging

from app.services.ingestion import extract_youtube_video_id

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# YouTube transcript (via youtube-transcript-api)
# ---------------------------------------------------------------------------

async def get_youtube_transcript(video_id: str, language: str = "de") -> str | None:
    """Fetch an existing transcript for a YouTube video.

    Tries *language* first, then "en", then any available transcript.
    Runs the blocking library in a thread-pool executor.
    Returns the transcript as a single string, or None if unavailable.
    """
    import asyncio

    from youtube_transcript_api import (
        NoTranscriptFound,
        TranscriptsDisabled,
        VideoUnavailable,
        YouTubeTranscriptApi,
    )

    def _fetch() -> str | None:
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        except (TranscriptsDisabled, VideoUnavailable, Exception) as exc:
            logger.debug("No transcript list for video %s: %s", video_id, exc)
            return None

        for lang in (language, "en"):
            try:
                segments = transcript_list.find_transcript([lang]).fetch()
                return " ".join(seg.get("text", "") for seg in segments).strip()
            except NoTranscriptFound:
                continue

        # Last resort: any available transcript (auto-generated, any language)
        try:
            segments = next(iter(transcript_list)).fetch()
            return " ".join(seg.get("text", "") for seg in segments).strip()
        except Exception as exc:
            logger.debug("Could not fetch any transcript for %s: %s", video_id, exc)
            return None

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _fetch)


# ---------------------------------------------------------------------------
# Whisper fallback (OpenAI audio transcription)
# ---------------------------------------------------------------------------

async def transcribe_with_whisper(audio_url: str) -> str:
    """Download audio from *audio_url* and transcribe it via OpenAI Whisper.

    Raises RuntimeError if the download or transcription fails.
    """
    import httpx
    from openai import AsyncOpenAI

    client = AsyncOpenAI()

    async with httpx.AsyncClient(timeout=60.0) as http:
        try:
            resp = await http.get(audio_url)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Failed to download audio from {audio_url}: {exc}") from exc

        audio_bytes = resp.content
        filename = audio_url.split("/")[-1].split("?")[0] or "audio.mp3"

    try:
        transcription = await client.audio.transcriptions.create(
            model="whisper-1",
            file=(filename, audio_bytes),
            response_format="text",
        )
    except Exception as exc:
        raise RuntimeError(f"Whisper transcription failed: {exc}") from exc

    return str(transcription).strip()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def get_transcript(source_url: str, language: str = "de") -> str | None:
    """Retrieve or generate a transcript for an episode URL.

    Strategy:
    - YouTube URL → youtube-transcript-api (free, no key required).
    - Podcast audio file (.mp3 / .m4a / …) → OpenAI Whisper.
    - Other URLs → None (unsupported).

    Returns the transcript text or None.
    """
    video_id = extract_youtube_video_id(source_url)

    if video_id:
        transcript = await get_youtube_transcript(video_id, language=language)
        if transcript:
            logger.info(
                "YouTube transcript for video %s (%d chars)", video_id, len(transcript)
            )
        else:
            logger.info("No YouTube transcript available for video %s", video_id)
        return transcript

    # Podcast: direct audio URL
    if source_url.lower().endswith((".mp3", ".m4a", ".ogg", ".wav", ".opus")):
        try:
            transcript = await transcribe_with_whisper(source_url)
            logger.info("Whisper transcript for %s (%d chars)", source_url, len(transcript))
            return transcript
        except RuntimeError as exc:
            logger.error("Whisper failed for %s: %s", source_url, exc)
            return None

    logger.warning("Cannot transcribe URL (unsupported format): %s", source_url)
    return None
