import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.creator_score import CreatorScore
    from app.models.episode import Episode


class Creator(Base):
    __tablename__ = "creators"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)  # "youtube" | "podcast"
    rss_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    youtube_channel_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="de")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    episodes: Mapped[list["Episode"]] = relationship(
        "Episode", back_populates="creator", lazy="select"
    )
    score: Mapped["CreatorScore | None"] = relationship(
        "CreatorScore", back_populates="creator", uselist=False, lazy="select"
    )
