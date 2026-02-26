"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-02-26 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the native PostgreSQL ENUM type before any table that uses it.
    recommendation_type_enum = postgresql.ENUM(
        "BUY", "HOLD", "SELL", name="recommendation_type", create_type=True
    )
    recommendation_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "creators",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("rss_url", sa.String(length=2048), nullable=True),
        sa.Column("youtube_channel_id", sa.String(length=255), nullable=True),
        sa.Column("language", sa.String(length=10), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "episodes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("creator_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("publish_date", sa.Date(), nullable=True),
        sa.Column("transcript", sa.Text(), nullable=True),
        sa.Column("source_url", sa.String(length=2048), nullable=True),
        sa.Column("processed", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["creator_id"], ["creators.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_episodes_creator_id", "episodes", ["creator_id"])

    op.create_table(
        "recommendations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("episode_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ticker", sa.String(length=20), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column(
            "type",
            sa.Enum("BUY", "HOLD", "SELL", name="recommendation_type"),
            nullable=False,
        ),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("sentence", sa.Text(), nullable=True),
        sa.Column("recommendation_date", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["episode_id"], ["episodes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_recommendations_episode_id", "recommendations", ["episode_id"])
    op.create_index("ix_recommendations_ticker", "recommendations", ["ticker"])

    op.create_table(
        "performance",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("recommendation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("price_at_recommendation", sa.Float(), nullable=True),
        sa.Column("return_1w", sa.Float(), nullable=True),
        sa.Column("return_1m", sa.Float(), nullable=True),
        sa.Column("return_3m", sa.Float(), nullable=True),
        sa.Column("return_6m", sa.Float(), nullable=True),
        sa.Column("return_12m", sa.Float(), nullable=True),
        sa.Column("benchmark_return_1m", sa.Float(), nullable=True),
        sa.Column("benchmark_return_3m", sa.Float(), nullable=True),
        sa.Column("benchmark_return_6m", sa.Float(), nullable=True),
        sa.Column("benchmark_return_12m", sa.Float(), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["recommendation_id"], ["recommendations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "recommendation_id", name="uq_performance_recommendation_id"
        ),
    )
    op.create_index(
        "ix_performance_recommendation_id", "performance", ["recommendation_id"]
    )

    op.create_table(
        "creator_scores",
        sa.Column("creator_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("total_picks", sa.Integer(), nullable=False),
        sa.Column("hit_rate", sa.Float(), nullable=True),
        sa.Column("avg_outperformance", sa.Float(), nullable=True),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["creator_id"], ["creators.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("creator_id"),
    )


def downgrade() -> None:
    op.drop_table("creator_scores")
    op.drop_index("ix_performance_recommendation_id", table_name="performance")
    op.drop_table("performance")
    op.drop_index("ix_recommendations_ticker", table_name="recommendations")
    op.drop_index("ix_recommendations_episode_id", table_name="recommendations")
    op.drop_table("recommendations")
    # Drop the ENUM type after the tables that reference it.
    op.execute("DROP TYPE IF EXISTS recommendation_type")
    op.drop_index("ix_episodes_creator_id", table_name="episodes")
    op.drop_table("episodes")
    op.drop_table("creators")
