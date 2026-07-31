"""Add simulation history, society, AI usage, and command coordination."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260731_0003"
down_revision: str | None = "20260731_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "world_settings",
        sa.Column("is_paused", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.alter_column("world_settings", "is_paused", server_default=None)

    op.create_table(
        "citizen_relationships",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("source_citizen_id", sa.Uuid(), nullable=False),
        sa.Column("target_citizen_id", sa.Uuid(), nullable=False),
        sa.Column("relationship_type", sa.String(32), nullable=False),
        sa.Column("strength", sa.Integer(), nullable=False),
        sa.Column("trust", sa.Integer(), nullable=False),
        sa.Column("familiarity", sa.Integer(), nullable=False),
        sa.Column("conflict", sa.Integer(), nullable=False),
        sa.Column("started_on", sa.Date(), nullable=False),
        sa.Column("last_interaction_on", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "source_citizen_id <> target_citizen_id", name="ck_relationship_no_self"
        ),
        sa.CheckConstraint("strength BETWEEN 0 AND 100", name="ck_relationship_strength"),
        sa.CheckConstraint("trust BETWEEN 0 AND 100", name="ck_relationship_trust"),
        sa.CheckConstraint("familiarity BETWEEN 0 AND 100", name="ck_relationship_familiarity"),
        sa.CheckConstraint("conflict BETWEEN 0 AND 100", name="ck_relationship_conflict"),
        sa.ForeignKeyConstraint(["world_id"], ["worlds.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_citizen_id"], ["citizens.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_citizen_id"], ["citizens.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_citizen_id",
            "target_citizen_id",
            "relationship_type",
            name="uq_citizen_relationship_edge",
        ),
    )
    op.create_index(
        "ix_relationships_world_source",
        "citizen_relationships",
        ["world_id", "source_citizen_id"],
    )
    op.create_index(
        "ix_relationships_world_target",
        "citizen_relationships",
        ["world_id", "target_citizen_id"],
    )

    op.create_table(
        "citizen_memories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("citizen_id", sa.Uuid(), nullable=False),
        sa.Column("related_event_id", sa.Uuid(), nullable=True),
        sa.Column("memory_type", sa.String(32), nullable=False),
        sa.Column("importance", sa.Integer(), nullable=False),
        sa.Column("emotional_score", sa.Integer(), nullable=False),
        sa.Column("recall_score", sa.Integer(), nullable=False),
        sa.Column("decay_basis_points", sa.Integer(), nullable=False),
        sa.Column("occurred_on", sa.Date(), nullable=False),
        sa.Column("related_citizen_ids", sa.JSON(), nullable=False),
        sa.Column("is_consolidated", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("importance BETWEEN 0 AND 100", name="ck_memories_importance"),
        sa.CheckConstraint("emotional_score BETWEEN -100 AND 100", name="ck_memories_emotion"),
        sa.CheckConstraint("recall_score BETWEEN 0 AND 100", name="ck_memories_recall"),
        sa.ForeignKeyConstraint(["world_id"], ["worlds.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["citizen_id"], ["citizens.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["related_event_id"], ["simulation_events.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_memories_citizen_recall",
        "citizen_memories",
        ["citizen_id", "importance", "recall_score"],
    )

    op.create_table(
        "simulation_outbox",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("channel", sa.String(40), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["world_id"], ["worlds.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["event_id"], ["simulation_events.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", name="uq_simulation_outbox_event"),
    )
    op.create_index(
        "ix_simulation_outbox_pending",
        "simulation_outbox",
        ["published_at", "created_at"],
    )

    op.create_table(
        "simulation_commands",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("sequence", sa.BigInteger(), nullable=False),
        sa.Column("command_type", sa.String(24), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("correlation_id", sa.Uuid(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["world_id"], ["worlds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("world_id", "sequence", name="uq_simulation_commands_world_sequence"),
    )
    op.create_index(
        "ix_simulation_commands_pending",
        "simulation_commands",
        ["world_id", "processed_at", "sequence"],
    )

    op.create_table(
        "ai_usage",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("simulation_date", sa.Date(), nullable=False),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("purpose", sa.String(60), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("estimated_cost_micros", sa.Integer(), nullable=False),
        sa.Column("cache_hit", sa.Boolean(), nullable=False),
        sa.Column("succeeded", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["world_id"], ["worlds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_usage_world_date", "ai_usage", ["world_id", "simulation_date"])
    op.create_index("ix_ai_usage_world_provider", "ai_usage", ["world_id", "provider", "model"])


def downgrade() -> None:
    op.drop_table("ai_usage")
    op.drop_table("simulation_commands")
    op.drop_table("simulation_outbox")
    op.drop_table("citizen_memories")
    op.drop_table("citizen_relationships")
    op.drop_column("world_settings", "is_paused")
