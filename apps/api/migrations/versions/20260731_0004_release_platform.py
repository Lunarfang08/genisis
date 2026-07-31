"""Release platform settings and audit records.

Revision ID: 20260731_0004
Revises: 20260731_0003
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260731_0004"
down_revision: str | None = "20260731_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "world_settings",
        sa.Column("initial_population", sa.Integer(), nullable=False, server_default="1000"),
    )
    op.add_column(
        "world_settings", sa.Column("city_count", sa.Integer(), nullable=False, server_default="3")
    )
    op.add_column(
        "world_settings",
        sa.Column("scenario", sa.String(length=40), nullable=False, server_default="balanced"),
    )
    op.add_column(
        "world_settings",
        sa.Column("scenario_config", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.create_check_constraint(
        "ck_world_settings_population", "world_settings", "initial_population BETWEEN 10 AND 50000"
    )
    op.create_check_constraint(
        "ck_world_settings_city_count", "world_settings", "city_count BETWEEN 1 AND 50"
    )


def downgrade() -> None:
    op.drop_constraint("ck_world_settings_city_count", "world_settings", type_="check")
    op.drop_constraint("ck_world_settings_population", "world_settings", type_="check")
    op.drop_column("world_settings", "scenario_config")
    op.drop_column("world_settings", "scenario")
    op.drop_column("world_settings", "city_count")
    op.drop_column("world_settings", "initial_population")
