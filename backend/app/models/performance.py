import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.recommendation import Recommendation


class Performance(Base):
    __tablename__ = "performance"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    recommendation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recommendations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    price_at_recommendation: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Stock returns
    return_1w: Mapped[float | None] = mapped_column(Float, nullable=True)
    return_1m: Mapped[float | None] = mapped_column(Float, nullable=True)
    return_3m: Mapped[float | None] = mapped_column(Float, nullable=True)
    return_6m: Mapped[float | None] = mapped_column(Float, nullable=True)
    return_12m: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Benchmark returns: S&P 500 (international) or DAX (German picks)
    benchmark_return_1m: Mapped[float | None] = mapped_column(Float, nullable=True)
    benchmark_return_3m: Mapped[float | None] = mapped_column(Float, nullable=True)
    benchmark_return_6m: Mapped[float | None] = mapped_column(Float, nullable=True)
    benchmark_return_12m: Mapped[float | None] = mapped_column(Float, nullable=True)

    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    recommendation: Mapped["Recommendation"] = relationship(
        "Recommendation", back_populates="performance"
    )
