"""Unit tests for scoring logic in app/utils/helpers.py."""
import pytest

from app.utils.helpers import (
    calculate_overall_score,
    calculate_relative_return,
    calculate_return,
    relative_return_to_score,
)


def test_calculate_return_positive():
    assert calculate_return(100.0, 110.0) == pytest.approx(0.10)


def test_calculate_return_negative():
    assert calculate_return(100.0, 90.0) == pytest.approx(-0.10)


def test_calculate_return_zero_start_raises():
    with pytest.raises(ValueError):
        calculate_return(0.0, 100.0)


def test_calculate_relative_return():
    assert calculate_relative_return(0.10, 0.05) == pytest.approx(0.05)


@pytest.mark.parametrize(
    "relative_return,expected_score",
    [
        (0.15, 1.0),   # > 10%
        (0.10, 0.8),   # boundary: 10% falls into 5–10% range (lower=0.05, upper=0.10 is exclusive)
        (0.07, 0.8),   # 5–10%
        (0.03, 0.6),   # 0–5%
        (-0.02, 0.4),  # -5–0%
        (-0.10, 0.1),  # < -5%
    ],
)
def test_relative_return_to_score(relative_return: float, expected_score: float):
    assert relative_return_to_score(relative_return) == expected_score


def test_calculate_overall_score():
    # (0.75 * 0.6) + (0.65 * 0.4) = 0.45 + 0.26 = 0.71
    result = calculate_overall_score(average_pick_score=0.75, hit_rate=0.65)
    assert result == pytest.approx(0.71)
