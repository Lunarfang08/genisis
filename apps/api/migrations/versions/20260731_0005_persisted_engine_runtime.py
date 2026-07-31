"""Persist deterministic engine runtime state.

Revision ID: 20260731_0005
Revises: 20260731_0004
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260731_0005"
down_revision: str | None = "20260731_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "world_settings",
        sa.Column("simulation_tick", sa.BigInteger(), nullable=False, server_default="0"),
    )
    op.add_column(
        "world_settings",
        sa.Column("event_sequence", sa.BigInteger(), nullable=False, server_default="0"),
    )
    op.add_column("world_settings", sa.Column("rng_state", sa.JSON(), nullable=True))
    op.add_column(
        "world_settings",
        sa.Column("social_cohesion", sa.Integer(), nullable=False, server_default="50"),
    )
    op.add_column(
        "world_settings",
        sa.Column("environmental_quality", sa.Integer(), nullable=False, server_default="70"),
    )
    op.create_check_constraint(
        "ck_world_settings_simulation_tick", "world_settings", "simulation_tick >= 0"
    )
    op.create_check_constraint(
        "ck_world_settings_event_sequence", "world_settings", "event_sequence >= 0"
    )
    op.create_check_constraint(
        "ck_world_settings_social_cohesion", "world_settings", "social_cohesion BETWEEN 0 AND 100"
    )
    op.create_check_constraint(
        "ck_world_settings_environmental_quality",
        "world_settings",
        "environmental_quality BETWEEN 0 AND 100",
    )


def downgrade() -> None:
    op.drop_constraint("ck_world_settings_environmental_quality", "world_settings", type_="check")
    op.drop_constraint("ck_world_settings_social_cohesion", "world_settings", type_="check")
    op.drop_constraint("ck_world_settings_event_sequence", "world_settings", type_="check")
    op.drop_constraint("ck_world_settings_simulation_tick", "world_settings", type_="check")
    op.drop_column("world_settings", "environmental_quality")
    op.drop_column("world_settings", "social_cohesion")
    op.drop_column("world_settings", "rng_state")
    op.drop_column("world_settings", "event_sequence")
    op.drop_column("world_settings", "simulation_tick")
