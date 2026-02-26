"""
Scoring service – Phase 3 implementation.
Calculates pick scores and aggregates creator scores.
See helpers.py for the scoring table and formulas.
"""
import uuid


async def update_performance(recommendation_id: uuid.UUID) -> None:
    """Fetch latest prices and recalculate all return periods for a recommendation."""
    raise NotImplementedError("Implemented in Phase 3")


async def recalculate_creator_score(creator_id: uuid.UUID) -> None:
    """Aggregate individual pick scores into creator overall_score and hit_rate."""
    raise NotImplementedError("Implemented in Phase 3")
