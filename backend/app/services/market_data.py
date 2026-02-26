"""
Market data service – Phase 3 implementation.
Fetches historical prices from Polygon.io or Alpha Vantage.
"""


async def get_price_at_date(ticker: str, date: str) -> float:
    """Return the closing price for a ticker on a given date (YYYY-MM-DD)."""
    raise NotImplementedError("Implemented in Phase 3")


async def get_benchmark_return(benchmark: str, start_date: str, end_date: str) -> float:
    """Return the percentage return for a benchmark (SPY or DAX) over a date range."""
    raise NotImplementedError("Implemented in Phase 3")
