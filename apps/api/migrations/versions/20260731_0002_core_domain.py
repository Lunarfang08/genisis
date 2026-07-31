"""Create the normalized civilization domain schema."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260731_0002"
down_revision: str | None = "20260727_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamps() -> tuple[sa.Column[object], sa.Column[object]]:
    return (
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def upgrade() -> None:
    op.add_column(
        "world_settings",
        sa.Column("start_date", sa.Date(), nullable=False, server_default=sa.text("'0001-01-01'")),
    )
    op.add_column(
        "world_settings",
        sa.Column(
            "simulation_date",
            sa.Date(),
            nullable=False,
            server_default=sa.text("'0001-01-01'"),
        ),
    )
    op.add_column(
        "world_settings",
        sa.Column("currency_code", sa.String(length=3), nullable=False, server_default="GNS"),
    )
    op.add_column(
        "world_settings",
        sa.Column("currency_scale", sa.Integer(), nullable=False, server_default="2"),
    )
    op.add_column(
        "world_settings",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    for column_name in (
        "start_date",
        "simulation_date",
        "currency_code",
        "currency_scale",
        "updated_at",
    ):
        op.alter_column("world_settings", column_name, server_default=None)
    op.create_check_constraint(
        "ck_world_settings_tick_rate", "world_settings", "tick_rate BETWEEN 1 AND 60"
    )
    op.create_check_constraint(
        "ck_world_settings_currency_scale",
        "world_settings",
        "currency_scale BETWEEN 0 AND 4",
    )

    op.create_table(
        "regions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("terrain", sa.String(length=40), nullable=False),
        sa.Column("area_km2", sa.Integer(), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(["world_id"], ["worlds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("world_id", "name", name="uq_regions_world_name"),
    )
    op.create_index("ix_regions_world_id", "regions", ["world_id"])
    op.create_index("ix_regions_world_created", "regions", ["world_id", "created_at"])

    op.create_table(
        "cities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("region_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("founded_year", sa.Integer(), nullable=False),
        sa.Column("latitude", sa.Numeric(precision=8, scale=5), nullable=False),
        sa.Column("longitude", sa.Numeric(precision=8, scale=5), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("founded_year >= 0", name="ck_cities_founded_year"),
        sa.ForeignKeyConstraint(["region_id"], ["regions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["world_id"], ["worlds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("region_id", "name", name="uq_cities_region_name"),
    )
    op.create_index("ix_cities_region_id", "cities", ["region_id"])
    op.create_index("ix_cities_world_id", "cities", ["world_id"])
    op.create_index("ix_cities_world_region", "cities", ["world_id", "region_id"])

    op.create_table(
        "households",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("city_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("wealth_minor", sa.BigInteger(), nullable=False),
        sa.Column("housing_status", sa.String(length=32), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("wealth_minor >= 0", name="ck_households_wealth"),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["world_id"], ["worlds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_households_city_id", "households", ["city_id"])
    op.create_index("ix_households_world_id", "households", ["world_id"])
    op.create_index("ix_households_world_city", "households", ["world_id", "city_id"])

    op.create_table(
        "occupations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("sector", sa.String(length=60), nullable=False),
        sa.Column("minimum_education", sa.String(length=24), nullable=False),
        sa.Column("base_salary_minor", sa.BigInteger(), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("base_salary_minor >= 0", name="ck_occupations_salary"),
        sa.CheckConstraint(
            "minimum_education IN ('none', 'primary', 'secondary', 'vocational', "
            "'tertiary', 'postgraduate')",
            name="ck_occupations_minimum_education",
        ),
        sa.ForeignKeyConstraint(["world_id"], ["worlds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("world_id", "name", name="uq_occupations_world_name"),
    )
    op.create_index("ix_occupations_world_id", "occupations", ["world_id"])

    op.create_table(
        "citizens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("city_id", sa.Uuid(), nullable=False),
        sa.Column("household_id", sa.Uuid(), nullable=True),
        sa.Column("occupation_id", sa.Uuid(), nullable=True),
        sa.Column("employer_business_id", sa.Uuid(), nullable=True),
        sa.Column("given_name", sa.String(length=80), nullable=False),
        sa.Column("family_name", sa.String(length=80), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=False),
        sa.Column("death_date", sa.Date(), nullable=True),
        sa.Column("biological_sex", sa.String(length=16), nullable=False),
        sa.Column("lifecycle_status", sa.String(length=16), nullable=False),
        sa.Column("education_level", sa.String(length=24), nullable=False),
        sa.Column("employment_status", sa.String(length=24), nullable=False),
        sa.Column("income_minor", sa.BigInteger(), nullable=False),
        sa.Column("wealth_minor", sa.BigInteger(), nullable=False),
        sa.Column("health", sa.Integer(), nullable=False),
        sa.Column("happiness", sa.Integer(), nullable=False),
        sa.Column("reputation", sa.Integer(), nullable=False),
        sa.Column("openness", sa.Integer(), nullable=False),
        sa.Column("conscientiousness", sa.Integer(), nullable=False),
        sa.Column("extraversion", sa.Integer(), nullable=False),
        sa.Column("agreeableness", sa.Integer(), nullable=False),
        sa.Column("neuroticism", sa.Integer(), nullable=False),
        sa.Column("dna_seed", sa.BigInteger(), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("health BETWEEN 0 AND 100", name="ck_citizens_health"),
        sa.CheckConstraint("happiness BETWEEN 0 AND 100", name="ck_citizens_happiness"),
        sa.CheckConstraint("reputation BETWEEN -100 AND 100", name="ck_citizens_reputation"),
        sa.CheckConstraint("openness BETWEEN 0 AND 100", name="ck_citizens_openness"),
        sa.CheckConstraint(
            "conscientiousness BETWEEN 0 AND 100", name="ck_citizens_conscientiousness"
        ),
        sa.CheckConstraint("extraversion BETWEEN 0 AND 100", name="ck_citizens_extraversion"),
        sa.CheckConstraint("agreeableness BETWEEN 0 AND 100", name="ck_citizens_agreeableness"),
        sa.CheckConstraint("neuroticism BETWEEN 0 AND 100", name="ck_citizens_neuroticism"),
        sa.CheckConstraint("income_minor >= 0", name="ck_citizens_income"),
        sa.CheckConstraint(
            "biological_sex IN ('female', 'male', 'intersex', 'unspecified')",
            name="ck_citizens_biological_sex",
        ),
        sa.CheckConstraint(
            "lifecycle_status IN ('child', 'adult', 'elder', 'deceased')",
            name="ck_citizens_lifecycle_status",
        ),
        sa.CheckConstraint(
            "education_level IN ('none', 'primary', 'secondary', 'vocational', "
            "'tertiary', 'postgraduate')",
            name="ck_citizens_education_level",
        ),
        sa.CheckConstraint(
            "employment_status IN ('not_in_workforce', 'unemployed', 'employed', "
            "'self_employed', 'retired')",
            name="ck_citizens_employment_status",
        ),
        sa.CheckConstraint(
            "(lifecycle_status = 'deceased' AND death_date IS NOT NULL) OR "
            "(lifecycle_status <> 'deceased' AND death_date IS NULL)",
            name="ck_citizens_lifecycle_death",
        ),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["occupation_id"], ["occupations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["world_id"], ["worlds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    for name, columns in (
        ("ix_citizens_world_id", ["world_id"]),
        ("ix_citizens_city_id", ["city_id"]),
        ("ix_citizens_household_id", ["household_id"]),
        ("ix_citizens_occupation_id", ["occupation_id"]),
        ("ix_citizens_employer_business_id", ["employer_business_id"]),
        ("ix_citizens_world_lifecycle", ["world_id", "lifecycle_status"]),
        ("ix_citizens_city_household", ["city_id", "household_id"]),
        (
            "ix_citizens_employment",
            ["world_id", "employment_status", "occupation_id"],
        ),
    ):
        op.create_index(name, "citizens", columns)

    op.create_table(
        "citizen_skills",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("citizen_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("proficiency", sa.Integer(), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("proficiency BETWEEN 0 AND 100", name="ck_citizen_skills_proficiency"),
        sa.ForeignKeyConstraint(["citizen_id"], ["citizens.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("citizen_id", "name", name="uq_citizen_skills_name"),
    )
    op.create_index("ix_citizen_skills_citizen_id", "citizen_skills", ["citizen_id"])

    op.create_table(
        "citizen_beliefs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("citizen_id", sa.Uuid(), nullable=False),
        sa.Column("topic", sa.String(length=80), nullable=False),
        sa.Column("position", sa.String(length=120), nullable=False),
        sa.Column("conviction", sa.Integer(), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("conviction BETWEEN 0 AND 100", name="ck_citizen_beliefs_conviction"),
        sa.ForeignKeyConstraint(["citizen_id"], ["citizens.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("citizen_id", "topic", name="uq_citizen_beliefs_topic"),
    )
    op.create_index("ix_citizen_beliefs_citizen_id", "citizen_beliefs", ["citizen_id"])

    op.create_table(
        "citizen_goals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("citizen_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=True),
        *_timestamps(),
        sa.CheckConstraint("priority BETWEEN 0 AND 100", name="ck_citizen_goals_priority"),
        sa.CheckConstraint(
            "status IN ('active', 'completed', 'abandoned')",
            name="ck_citizen_goals_status",
        ),
        sa.ForeignKeyConstraint(["citizen_id"], ["citizens.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_citizen_goals_citizen_id", "citizen_goals", ["citizen_id"])
    op.create_index(
        "ix_citizen_goals_active", "citizen_goals", ["citizen_id", "status", "priority"]
    )

    op.create_table(
        "businesses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("city_id", sa.Uuid(), nullable=False),
        sa.Column("owner_citizen_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("industry", sa.String(length=60), nullable=False),
        sa.Column("cash_minor", sa.BigInteger(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("founded_on", sa.Date(), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("cash_minor >= 0", name="ck_businesses_cash"),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["owner_citizen_id"], ["citizens.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["world_id"], ["worlds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("city_id", "name", name="uq_businesses_city_name"),
    )
    op.create_index("ix_businesses_world_id", "businesses", ["world_id"])
    op.create_index("ix_businesses_city_id", "businesses", ["city_id"])
    op.create_index("ix_businesses_owner_citizen_id", "businesses", ["owner_citizen_id"])
    op.create_index("ix_businesses_world_city", "businesses", ["world_id", "city_id"])
    op.create_foreign_key(
        "fk_citizens_employer_business_id",
        "citizens",
        "businesses",
        ["employer_business_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "governments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("region_id", sa.Uuid(), nullable=True),
        sa.Column("city_id", sa.Uuid(), nullable=True),
        sa.Column("leader_citizen_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("scope", sa.String(length=16), nullable=False),
        sa.Column("government_type", sa.String(length=40), nullable=False),
        sa.Column("treasury_minor", sa.BigInteger(), nullable=False),
        sa.Column("term_started_on", sa.Date(), nullable=True),
        sa.Column("term_ends_on", sa.Date(), nullable=True),
        *_timestamps(),
        sa.CheckConstraint("scope IN ('world', 'region', 'city')", name="ck_governments_scope"),
        sa.CheckConstraint(
            "(scope = 'world' AND region_id IS NULL AND city_id IS NULL) OR "
            "(scope = 'region' AND region_id IS NOT NULL AND city_id IS NULL) OR "
            "(scope = 'city' AND city_id IS NOT NULL)",
            name="ck_governments_scope_target",
        ),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["leader_citizen_id"], ["citizens.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["region_id"], ["regions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["world_id"], ["worlds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("world_id", "name", name="uq_governments_world_name"),
    )
    for name, columns in (
        ("ix_governments_world_id", ["world_id"]),
        ("ix_governments_region_id", ["region_id"]),
        ("ix_governments_city_id", ["city_id"]),
        ("ix_governments_leader_citizen_id", ["leader_citizen_id"]),
        ("ix_governments_world_scope", ["world_id", "scope"]),
    ):
        op.create_index(name, "governments", columns)

    op.create_table(
        "laws",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("government_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("enacted_on", sa.Date(), nullable=True),
        sa.Column("repealed_on", sa.Date(), nullable=True),
        *_timestamps(),
        sa.CheckConstraint("status IN ('proposed', 'active', 'repealed')", name="ck_laws_status"),
        sa.CheckConstraint(
            "(status = 'repealed' AND repealed_on IS NOT NULL) OR "
            "(status <> 'repealed' AND repealed_on IS NULL)",
            name="ck_laws_repeal_date",
        ),
        sa.ForeignKeyConstraint(["government_id"], ["governments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["world_id"], ["worlds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("government_id", "code", name="uq_laws_government_code"),
    )
    op.create_index("ix_laws_world_id", "laws", ["world_id"])
    op.create_index("ix_laws_government_id", "laws", ["government_id"])
    op.create_index("ix_laws_world_status", "laws", ["world_id", "status"])

    op.create_table(
        "simulation_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("sequence", sa.BigInteger(), nullable=False),
        sa.Column("simulation_date", sa.Date(), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("engine_version", sa.String(length=32), nullable=False),
        sa.Column("actor_citizen_id", sa.Uuid(), nullable=True),
        sa.Column("target_citizen_id", sa.Uuid(), nullable=True),
        sa.Column("city_id", sa.Uuid(), nullable=True),
        sa.Column("causation_id", sa.Uuid(), nullable=True),
        sa.Column("correlation_id", sa.Uuid(), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("importance", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("sequence > 0", name="ck_simulation_events_sequence"),
        sa.CheckConstraint("importance BETWEEN 0 AND 100", name="ck_simulation_events_importance"),
        sa.CheckConstraint(
            "severity IN ('info', 'notice', 'warning', 'critical')",
            name="ck_simulation_events_severity",
        ),
        sa.ForeignKeyConstraint(["actor_citizen_id"], ["citizens.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["target_citizen_id"], ["citizens.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["world_id"], ["worlds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("world_id", "sequence", name="uq_simulation_events_world_sequence"),
    )
    for name, columns in (
        ("ix_simulation_events_world_id", ["world_id"]),
        ("ix_simulation_events_actor_citizen_id", ["actor_citizen_id"]),
        ("ix_simulation_events_target_citizen_id", ["target_citizen_id"]),
        ("ix_simulation_events_city_id", ["city_id"]),
        ("ix_simulation_events_causation_id", ["causation_id"]),
        ("ix_simulation_events_correlation_id", ["correlation_id"]),
        (
            "ix_simulation_events_world_time",
            ["world_id", "simulation_date", "sequence"],
        ),
        (
            "ix_simulation_events_world_category",
            ["world_id", "category", "sequence"],
        ),
        ("ix_simulation_events_actor", ["world_id", "actor_citizen_id", "sequence"]),
    ):
        op.create_index(name, "simulation_events", columns)

    op.create_table(
        "simulation_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("event_sequence", sa.BigInteger(), nullable=False),
        sa.Column("simulation_date", sa.Date(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("engine_version", sa.String(length=32), nullable=False),
        sa.Column("rng_state", sa.JSON(), nullable=False),
        sa.Column("state", sa.JSON(), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("event_sequence >= 0", name="ck_simulation_snapshots_sequence"),
        sa.ForeignKeyConstraint(["world_id"], ["worlds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "world_id",
            "event_sequence",
            name="uq_simulation_snapshots_world_sequence",
        ),
    )
    op.create_index("ix_simulation_snapshots_world_id", "simulation_snapshots", ["world_id"])
    op.create_index(
        "ix_simulation_snapshots_world_date",
        "simulation_snapshots",
        ["world_id", "simulation_date"],
    )

    op.create_table(
        "world_metrics",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("world_id", sa.Uuid(), nullable=False),
        sa.Column("simulation_date", sa.Date(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("scope", sa.String(length=20), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("value", sa.Numeric(precision=24, scale=8), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=False),
        sa.Column("labels", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["world_id"], ["worlds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "world_id",
            "simulation_date",
            "name",
            "scope",
            "entity_id",
            name="uq_world_metrics_point",
        ),
    )
    op.create_index("ix_world_metrics_world_id", "world_metrics", ["world_id"])
    op.create_index(
        "ix_world_metrics_world_name_date",
        "world_metrics",
        ["world_id", "name", "simulation_date"],
    )


def downgrade() -> None:
    op.drop_table("world_metrics")
    op.drop_table("simulation_snapshots")
    op.drop_table("simulation_events")
    op.drop_table("laws")
    op.drop_table("governments")
    op.drop_constraint("fk_citizens_employer_business_id", "citizens", type_="foreignkey")
    op.drop_table("businesses")
    op.drop_table("citizen_goals")
    op.drop_table("citizen_beliefs")
    op.drop_table("citizen_skills")
    op.drop_table("citizens")
    op.drop_table("occupations")
    op.drop_table("households")
    op.drop_table("cities")
    op.drop_table("regions")
    op.drop_constraint("ck_world_settings_currency_scale", "world_settings", type_="check")
    op.drop_constraint("ck_world_settings_tick_rate", "world_settings", type_="check")
    op.drop_column("world_settings", "updated_at")
    op.drop_column("world_settings", "currency_scale")
    op.drop_column("world_settings", "currency_code")
    op.drop_column("world_settings", "simulation_date")
    op.drop_column("world_settings", "start_date")
