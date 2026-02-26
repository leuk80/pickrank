"""Unit tests for NLP extraction – Phase 2."""
import pytest


@pytest.mark.asyncio
async def test_extract_recommendations_not_implemented():
    from app.services.nlp_extraction import extract_recommendations

    with pytest.raises(NotImplementedError):
        await extract_recommendations("Apple is a buy at current prices.")
