"""
Shared utility functions used across the application.
"""
from datetime import date, datetime, timezone


def utc_now() -> datetime:
    """Return current UTC datetime as timezone-aware."""
    return datetime.now(tz=timezone.utc)


def date_to_datetime(d: date) -> datetime:
    """Convert a naive date to UTC midnight datetime."""
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)


def calculate_return(price_start: float, price_end: float) -> float:
    """Calculate simple percentage return between two prices.

    Returns the fractional return, e.g. 0.05 means +5%.
    Raises ValueError if price_start is zero.
    """
    if price_start == 0:
        raise ValueError("price_start cannot be zero")
    return (price_end - price_start) / price_start


def calculate_relative_return(stock_return: float, benchmark_return: float) -> float:
    """Calculate the relative return of a stock vs its benchmark.

    relative_return = stock_return - benchmark_return
    Benchmarks: S&P 500 (international picks), DAX (German picks)
    """
    return stock_return - benchmark_return


# Scoring table as defined in CLAUDE.md
# Each entry: (lower_inclusive, upper_exclusive, score)
_SCORE_TABLE: list[tuple[float, float, float]] = [
    (0.10, float("inf"), 1.0),
    (0.05, 0.10, 0.8),
    (0.00, 0.05, 0.6),
    (-0.05, 0.00, 0.4),
    (float("-inf"), -0.05, 0.1),
]


def relative_return_to_score(relative_return: float) -> float:
    """Convert a relative return to a pick score using the scoring table.

    Scoring table (relative return → score):
      > 10%   → 1.0
      5–10%   → 0.8
      0–5%    → 0.6
      -5–0%   → 0.4
      < -5%   → 0.1
    """
    for lower, upper, score in _SCORE_TABLE:
        if lower <= relative_return < upper:
            return score
    return 0.1  # fallback (should never be reached)


def calculate_overall_score(average_pick_score: float, hit_rate: float) -> float:
    """Compute a creator's overall_score.

    overall_score = (average_pick_score × 0.6) + (hit_rate × 0.4)
    """
    return (average_pick_score * 0.6) + (hit_rate * 0.4)
