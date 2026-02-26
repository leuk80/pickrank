# Import all models so Alembic's env.py sees all table metadata via a single import.
from app.models.creator import Creator
from app.models.creator_score import CreatorScore
from app.models.episode import Episode
from app.models.performance import Performance
from app.models.recommendation import Recommendation

__all__ = [
    "Creator",
    "CreatorScore",
    "Episode",
    "Performance",
    "Recommendation",
]
