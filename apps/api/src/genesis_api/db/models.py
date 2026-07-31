from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from genesis_api.db.base import Base
from genesis_api.domain.types import (
    BiologicalSex,
    EducationLevel,
    EmploymentStatus,
    EventSeverity,
    GoalStatus,
    GovernmentScope,
    LawStatus,
    LifecycleStatus,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(80))
    password_hash: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    worlds: Mapped[list["World"]] = relationship(back_populates="owner", cascade="all, delete")


class RefreshSession(Base):
    __tablename__ = "refresh_sessions"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    family_id: Mapped[UUID] = mapped_column(Uuid, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    replaced_by_id: Mapped[UUID | None] = mapped_column(Uuid)


class World(Base):
    __tablename__ = "worlds"
    __table_args__ = (Index("ix_worlds_owner_created", "owner_id", "created_at"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    owner: Mapped[User] = relationship(back_populates="worlds")
    settings: Mapped["WorldSettings"] = relationship(
        back_populates="world", cascade="all, delete-orphan", uselist=False
    )
    regions: Mapped[list["Region"]] = relationship(back_populates="world", cascade="all, delete")
    occupations: Mapped[list["Occupation"]] = relationship(
        back_populates="world", cascade="all, delete"
    )


class WorldSettings(Base):
    __tablename__ = "world_settings"
    __table_args__ = (
        CheckConstraint("tick_rate BETWEEN 1 AND 60", name="ck_world_settings_tick_rate"),
        CheckConstraint("currency_scale BETWEEN 0 AND 4", name="ck_world_settings_currency_scale"),
    )

    world_id: Mapped[UUID] = mapped_column(
        ForeignKey("worlds.id", ondelete="CASCADE"), primary_key=True
    )
    seed: Mapped[int] = mapped_column()
    tick_rate: Mapped[int] = mapped_column(default=1)
    initial_population: Mapped[int] = mapped_column(default=1000)
    city_count: Mapped[int] = mapped_column(default=3)
    scenario: Mapped[str] = mapped_column(String(40), default="balanced")
    scenario_config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    simulation_tick: Mapped[int] = mapped_column(BigInteger, default=0)
    event_sequence: Mapped[int] = mapped_column(BigInteger, default=0)
    rng_state: Mapped[list[Any] | None] = mapped_column(JSON)
    social_cohesion: Mapped[int] = mapped_column(default=50)
    environmental_quality: Mapped[int] = mapped_column(default=70)
    start_date: Mapped[date] = mapped_column(Date, default=date(1, 1, 1))
    simulation_date: Mapped[date] = mapped_column(Date, default=date(1, 1, 1))
    is_paused: Mapped[bool] = mapped_column(Boolean, default=True)
    currency_code: Mapped[str] = mapped_column(String(3), default="GNS")
    currency_scale: Mapped[int] = mapped_column(default=2)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    world: Mapped[World] = relationship(back_populates="settings")


class Region(Base):
    __tablename__ = "regions"
    __table_args__ = (
        UniqueConstraint("world_id", "name", name="uq_regions_world_name"),
        Index("ix_regions_world_created", "world_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    world_id: Mapped[UUID] = mapped_column(ForeignKey("worlds.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    terrain: Mapped[str] = mapped_column(String(40), default="temperate")
    area_km2: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    world: Mapped[World] = relationship(back_populates="regions")
    cities: Mapped[list["City"]] = relationship(back_populates="region", cascade="all, delete")


class City(Base):
    __tablename__ = "cities"
    __table_args__ = (
        UniqueConstraint("region_id", "name", name="uq_cities_region_name"),
        CheckConstraint("founded_year >= 0", name="ck_cities_founded_year"),
        Index("ix_cities_world_region", "world_id", "region_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    world_id: Mapped[UUID] = mapped_column(ForeignKey("worlds.id", ondelete="CASCADE"), index=True)
    region_id: Mapped[UUID] = mapped_column(
        ForeignKey("regions.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120))
    founded_year: Mapped[int] = mapped_column(default=0)
    latitude: Mapped[Decimal] = mapped_column(Numeric(8, 5), default=Decimal("0"))
    longitude: Mapped[Decimal] = mapped_column(Numeric(8, 5), default=Decimal("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    region: Mapped[Region] = relationship(back_populates="cities")
    households: Mapped[list["Household"]] = relationship(
        back_populates="city", cascade="all, delete"
    )


class Household(Base):
    __tablename__ = "households"
    __table_args__ = (
        CheckConstraint("wealth_minor >= 0", name="ck_households_wealth"),
        Index("ix_households_world_city", "world_id", "city_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    world_id: Mapped[UUID] = mapped_column(ForeignKey("worlds.id", ondelete="CASCADE"), index=True)
    city_id: Mapped[UUID] = mapped_column(ForeignKey("cities.id", ondelete="RESTRICT"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    wealth_minor: Mapped[int] = mapped_column(BigInteger, default=0)
    housing_status: Mapped[str] = mapped_column(String(32), default="housed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    city: Mapped[City] = relationship(back_populates="households")
    citizens: Mapped[list["Citizen"]] = relationship(back_populates="household")


class Occupation(Base):
    __tablename__ = "occupations"
    __table_args__ = (
        UniqueConstraint("world_id", "name", name="uq_occupations_world_name"),
        CheckConstraint("base_salary_minor >= 0", name="ck_occupations_salary"),
        CheckConstraint(
            "minimum_education IN ('none', 'primary', 'secondary', 'vocational', "
            "'tertiary', 'postgraduate')",
            name="ck_occupations_minimum_education",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    world_id: Mapped[UUID] = mapped_column(ForeignKey("worlds.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    sector: Mapped[str] = mapped_column(String(60))
    minimum_education: Mapped[str] = mapped_column(String(24), default=EducationLevel.NONE.value)
    base_salary_minor: Mapped[int] = mapped_column(BigInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    world: Mapped[World] = relationship(back_populates="occupations")


class Business(Base):
    __tablename__ = "businesses"
    __table_args__ = (
        UniqueConstraint("city_id", "name", name="uq_businesses_city_name"),
        CheckConstraint("cash_minor >= 0", name="ck_businesses_cash"),
        Index("ix_businesses_world_city", "world_id", "city_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    world_id: Mapped[UUID] = mapped_column(ForeignKey("worlds.id", ondelete="CASCADE"), index=True)
    city_id: Mapped[UUID] = mapped_column(ForeignKey("cities.id", ondelete="RESTRICT"), index=True)
    owner_citizen_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("citizens.id", ondelete="SET NULL"), index=True
    )
    name: Mapped[str] = mapped_column(String(120))
    industry: Mapped[str] = mapped_column(String(60))
    cash_minor: Mapped[int] = mapped_column(BigInteger, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    founded_on: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class Citizen(Base):
    __tablename__ = "citizens"
    __table_args__ = (
        CheckConstraint("health BETWEEN 0 AND 100", name="ck_citizens_health"),
        CheckConstraint("happiness BETWEEN 0 AND 100", name="ck_citizens_happiness"),
        CheckConstraint("reputation BETWEEN -100 AND 100", name="ck_citizens_reputation"),
        CheckConstraint("openness BETWEEN 0 AND 100", name="ck_citizens_openness"),
        CheckConstraint(
            "conscientiousness BETWEEN 0 AND 100", name="ck_citizens_conscientiousness"
        ),
        CheckConstraint("extraversion BETWEEN 0 AND 100", name="ck_citizens_extraversion"),
        CheckConstraint("agreeableness BETWEEN 0 AND 100", name="ck_citizens_agreeableness"),
        CheckConstraint("neuroticism BETWEEN 0 AND 100", name="ck_citizens_neuroticism"),
        CheckConstraint("income_minor >= 0", name="ck_citizens_income"),
        CheckConstraint(
            "biological_sex IN ('female', 'male', 'intersex', 'unspecified')",
            name="ck_citizens_biological_sex",
        ),
        CheckConstraint(
            "lifecycle_status IN ('child', 'adult', 'elder', 'deceased')",
            name="ck_citizens_lifecycle_status",
        ),
        CheckConstraint(
            "education_level IN ('none', 'primary', 'secondary', 'vocational', "
            "'tertiary', 'postgraduate')",
            name="ck_citizens_education_level",
        ),
        CheckConstraint(
            "employment_status IN ('not_in_workforce', 'unemployed', 'employed', "
            "'self_employed', 'retired')",
            name="ck_citizens_employment_status",
        ),
        CheckConstraint(
            "(lifecycle_status = 'deceased' AND death_date IS NOT NULL) OR "
            "(lifecycle_status <> 'deceased' AND death_date IS NULL)",
            name="ck_citizens_lifecycle_death",
        ),
        Index("ix_citizens_world_lifecycle", "world_id", "lifecycle_status"),
        Index("ix_citizens_city_household", "city_id", "household_id"),
        Index("ix_citizens_employment", "world_id", "employment_status", "occupation_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    world_id: Mapped[UUID] = mapped_column(ForeignKey("worlds.id", ondelete="CASCADE"), index=True)
    city_id: Mapped[UUID] = mapped_column(ForeignKey("cities.id", ondelete="RESTRICT"), index=True)
    household_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("households.id", ondelete="SET NULL"), index=True
    )
    occupation_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("occupations.id", ondelete="SET NULL"), index=True
    )
    employer_business_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("businesses.id", ondelete="SET NULL"), index=True
    )
    given_name: Mapped[str] = mapped_column(String(80))
    family_name: Mapped[str] = mapped_column(String(80))
    birth_date: Mapped[date] = mapped_column(Date)
    death_date: Mapped[date | None] = mapped_column(Date)
    biological_sex: Mapped[str] = mapped_column(String(16), default=BiologicalSex.UNSPECIFIED.value)
    lifecycle_status: Mapped[str] = mapped_column(String(16), default=LifecycleStatus.ADULT.value)
    education_level: Mapped[str] = mapped_column(String(24), default=EducationLevel.NONE.value)
    employment_status: Mapped[str] = mapped_column(
        String(24), default=EmploymentStatus.NOT_IN_WORKFORCE.value
    )
    income_minor: Mapped[int] = mapped_column(BigInteger, default=0)
    wealth_minor: Mapped[int] = mapped_column(BigInteger, default=0)
    health: Mapped[int] = mapped_column(default=100)
    happiness: Mapped[int] = mapped_column(default=50)
    reputation: Mapped[int] = mapped_column(default=0)
    openness: Mapped[int] = mapped_column(default=50)
    conscientiousness: Mapped[int] = mapped_column(default=50)
    extraversion: Mapped[int] = mapped_column(default=50)
    agreeableness: Mapped[int] = mapped_column(default=50)
    neuroticism: Mapped[int] = mapped_column(default=50)
    dna_seed: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    household: Mapped[Household | None] = relationship(back_populates="citizens")
    skills: Mapped[list["CitizenSkill"]] = relationship(
        back_populates="citizen", cascade="all, delete-orphan"
    )
    beliefs: Mapped[list["CitizenBelief"]] = relationship(
        back_populates="citizen", cascade="all, delete-orphan"
    )
    goals: Mapped[list["CitizenGoal"]] = relationship(
        back_populates="citizen", cascade="all, delete-orphan"
    )
    memories: Mapped[list["CitizenMemory"]] = relationship(
        back_populates="citizen", cascade="all, delete-orphan"
    )

    @property
    def full_name(self) -> str:
        return f"{self.given_name} {self.family_name}"

    def age_on(self, on_date: date) -> int:
        years = on_date.year - self.birth_date.year
        if (on_date.month, on_date.day) < (self.birth_date.month, self.birth_date.day):
            years -= 1
        return years


class CitizenSkill(Base):
    __tablename__ = "citizen_skills"
    __table_args__ = (
        UniqueConstraint("citizen_id", "name", name="uq_citizen_skills_name"),
        CheckConstraint("proficiency BETWEEN 0 AND 100", name="ck_citizen_skills_proficiency"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    citizen_id: Mapped[UUID] = mapped_column(
        ForeignKey("citizens.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(80))
    proficiency: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    citizen: Mapped[Citizen] = relationship(back_populates="skills")


class CitizenBelief(Base):
    __tablename__ = "citizen_beliefs"
    __table_args__ = (
        UniqueConstraint("citizen_id", "topic", name="uq_citizen_beliefs_topic"),
        CheckConstraint("conviction BETWEEN 0 AND 100", name="ck_citizen_beliefs_conviction"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    citizen_id: Mapped[UUID] = mapped_column(
        ForeignKey("citizens.id", ondelete="CASCADE"), index=True
    )
    topic: Mapped[str] = mapped_column(String(80))
    position: Mapped[str] = mapped_column(String(120))
    conviction: Mapped[int] = mapped_column(default=50)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    citizen: Mapped[Citizen] = relationship(back_populates="beliefs")


class CitizenGoal(Base):
    __tablename__ = "citizen_goals"
    __table_args__ = (
        CheckConstraint("priority BETWEEN 0 AND 100", name="ck_citizen_goals_priority"),
        CheckConstraint(
            "status IN ('active', 'completed', 'abandoned')", name="ck_citizen_goals_status"
        ),
        Index("ix_citizen_goals_active", "citizen_id", "status", "priority"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    citizen_id: Mapped[UUID] = mapped_column(
        ForeignKey("citizens.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(16), default=GoalStatus.ACTIVE.value)
    priority: Mapped[int] = mapped_column(default=50)
    target_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    citizen: Mapped[Citizen] = relationship(back_populates="goals")


class CitizenRelationship(Base):
    __tablename__ = "citizen_relationships"
    __table_args__ = (
        UniqueConstraint(
            "source_citizen_id",
            "target_citizen_id",
            "relationship_type",
            name="uq_citizen_relationship_edge",
        ),
        CheckConstraint("source_citizen_id <> target_citizen_id", name="ck_relationship_no_self"),
        CheckConstraint("strength BETWEEN 0 AND 100", name="ck_relationship_strength"),
        CheckConstraint("trust BETWEEN 0 AND 100", name="ck_relationship_trust"),
        CheckConstraint("familiarity BETWEEN 0 AND 100", name="ck_relationship_familiarity"),
        CheckConstraint("conflict BETWEEN 0 AND 100", name="ck_relationship_conflict"),
        Index("ix_relationships_world_source", "world_id", "source_citizen_id"),
        Index("ix_relationships_world_target", "world_id", "target_citizen_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    world_id: Mapped[UUID] = mapped_column(ForeignKey("worlds.id", ondelete="CASCADE"))
    source_citizen_id: Mapped[UUID] = mapped_column(ForeignKey("citizens.id", ondelete="CASCADE"))
    target_citizen_id: Mapped[UUID] = mapped_column(ForeignKey("citizens.id", ondelete="CASCADE"))
    relationship_type: Mapped[str] = mapped_column(String(32))
    strength: Mapped[int] = mapped_column(default=50)
    trust: Mapped[int] = mapped_column(default=50)
    familiarity: Mapped[int] = mapped_column(default=1)
    conflict: Mapped[int] = mapped_column(default=0)
    started_on: Mapped[date] = mapped_column(Date)
    last_interaction_on: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class CitizenMemory(Base):
    __tablename__ = "citizen_memories"
    __table_args__ = (
        CheckConstraint("importance BETWEEN 0 AND 100", name="ck_memories_importance"),
        CheckConstraint("emotional_score BETWEEN -100 AND 100", name="ck_memories_emotion"),
        CheckConstraint("recall_score BETWEEN 0 AND 100", name="ck_memories_recall"),
        Index("ix_memories_citizen_recall", "citizen_id", "importance", "recall_score"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    world_id: Mapped[UUID] = mapped_column(ForeignKey("worlds.id", ondelete="CASCADE"))
    citizen_id: Mapped[UUID] = mapped_column(ForeignKey("citizens.id", ondelete="CASCADE"))
    related_event_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("simulation_events.id", ondelete="SET NULL")
    )
    memory_type: Mapped[str] = mapped_column(String(32))
    importance: Mapped[int] = mapped_column()
    emotional_score: Mapped[int] = mapped_column()
    recall_score: Mapped[int] = mapped_column(default=100)
    decay_basis_points: Mapped[int] = mapped_column(default=100)
    occurred_on: Mapped[date] = mapped_column(Date)
    related_citizen_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_consolidated: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    citizen: Mapped[Citizen] = relationship(back_populates="memories")


class Government(Base):
    __tablename__ = "governments"
    __table_args__ = (
        UniqueConstraint("world_id", "name", name="uq_governments_world_name"),
        CheckConstraint("scope IN ('world', 'region', 'city')", name="ck_governments_scope"),
        CheckConstraint(
            "(scope = 'world' AND region_id IS NULL AND city_id IS NULL) OR "
            "(scope = 'region' AND region_id IS NOT NULL AND city_id IS NULL) OR "
            "(scope = 'city' AND city_id IS NOT NULL)",
            name="ck_governments_scope_target",
        ),
        Index("ix_governments_world_scope", "world_id", "scope"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    world_id: Mapped[UUID] = mapped_column(ForeignKey("worlds.id", ondelete="CASCADE"), index=True)
    region_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("regions.id", ondelete="CASCADE"), index=True
    )
    city_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("cities.id", ondelete="CASCADE"), index=True
    )
    leader_citizen_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("citizens.id", ondelete="SET NULL"), index=True
    )
    name: Mapped[str] = mapped_column(String(120))
    scope: Mapped[str] = mapped_column(String(16), default=GovernmentScope.WORLD.value)
    government_type: Mapped[str] = mapped_column(String(40), default="democracy")
    treasury_minor: Mapped[int] = mapped_column(BigInteger, default=0)
    term_started_on: Mapped[date | None] = mapped_column(Date)
    term_ends_on: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    laws: Mapped[list["Law"]] = relationship(
        back_populates="government", cascade="all, delete-orphan"
    )


class Law(Base):
    __tablename__ = "laws"
    __table_args__ = (
        UniqueConstraint("government_id", "code", name="uq_laws_government_code"),
        CheckConstraint("status IN ('proposed', 'active', 'repealed')", name="ck_laws_status"),
        CheckConstraint(
            "(status = 'repealed' AND repealed_on IS NOT NULL) OR "
            "(status <> 'repealed' AND repealed_on IS NULL)",
            name="ck_laws_repeal_date",
        ),
        Index("ix_laws_world_status", "world_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    world_id: Mapped[UUID] = mapped_column(ForeignKey("worlds.id", ondelete="CASCADE"), index=True)
    government_id: Mapped[UUID] = mapped_column(
        ForeignKey("governments.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(40))
    title: Mapped[str] = mapped_column(String(160))
    text: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default=LawStatus.PROPOSED.value)
    enacted_on: Mapped[date | None] = mapped_column(Date)
    repealed_on: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    government: Mapped[Government] = relationship(back_populates="laws")


class SimulationEvent(Base):
    __tablename__ = "simulation_events"
    __table_args__ = (
        UniqueConstraint("world_id", "sequence", name="uq_simulation_events_world_sequence"),
        CheckConstraint("sequence > 0", name="ck_simulation_events_sequence"),
        CheckConstraint("importance BETWEEN 0 AND 100", name="ck_simulation_events_importance"),
        CheckConstraint(
            "severity IN ('info', 'notice', 'warning', 'critical')",
            name="ck_simulation_events_severity",
        ),
        Index("ix_simulation_events_world_time", "world_id", "simulation_date", "sequence"),
        Index("ix_simulation_events_world_category", "world_id", "category", "sequence"),
        Index("ix_simulation_events_actor", "world_id", "actor_citizen_id", "sequence"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    world_id: Mapped[UUID] = mapped_column(ForeignKey("worlds.id", ondelete="CASCADE"), index=True)
    sequence: Mapped[int] = mapped_column(BigInteger)
    simulation_date: Mapped[date] = mapped_column(Date)
    category: Mapped[str] = mapped_column(String(40))
    event_type: Mapped[str] = mapped_column(String(80))
    schema_version: Mapped[int] = mapped_column(default=1)
    engine_version: Mapped[str] = mapped_column(String(32), default="unversioned")
    actor_citizen_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("citizens.id", ondelete="SET NULL"), index=True
    )
    target_citizen_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("citizens.id", ondelete="SET NULL"), index=True
    )
    city_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("cities.id", ondelete="SET NULL"), index=True
    )
    causation_id: Mapped[UUID | None] = mapped_column(Uuid, index=True)
    correlation_id: Mapped[UUID] = mapped_column(Uuid, index=True, default=uuid4)
    severity: Mapped[str] = mapped_column(String(16), default=EventSeverity.INFO.value)
    importance: Mapped[int] = mapped_column(default=0)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class SimulationOutbox(Base):
    __tablename__ = "simulation_outbox"
    __table_args__ = (
        UniqueConstraint("event_id", name="uq_simulation_outbox_event"),
        Index("ix_simulation_outbox_pending", "published_at", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    world_id: Mapped[UUID] = mapped_column(ForeignKey("worlds.id", ondelete="CASCADE"))
    event_id: Mapped[UUID] = mapped_column(ForeignKey("simulation_events.id", ondelete="CASCADE"))
    channel: Mapped[str] = mapped_column(String(40))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    attempts: Mapped[int] = mapped_column(default=0)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class SimulationCommand(Base):
    __tablename__ = "simulation_commands"
    __table_args__ = (
        UniqueConstraint("world_id", "sequence", name="uq_simulation_commands_world_sequence"),
        Index("ix_simulation_commands_pending", "world_id", "processed_at", "sequence"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    world_id: Mapped[UUID] = mapped_column(ForeignKey("worlds.id", ondelete="CASCADE"))
    sequence: Mapped[int] = mapped_column(BigInteger)
    command_type: Mapped[str] = mapped_column(String(24))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    correlation_id: Mapped[UUID] = mapped_column(Uuid, default=uuid4)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class AIUsage(Base):
    __tablename__ = "ai_usage"
    __table_args__ = (
        Index("ix_ai_usage_world_date", "world_id", "simulation_date"),
        Index("ix_ai_usage_world_provider", "world_id", "provider", "model"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    world_id: Mapped[UUID] = mapped_column(ForeignKey("worlds.id", ondelete="CASCADE"))
    simulation_date: Mapped[date] = mapped_column(Date)
    provider: Mapped[str] = mapped_column(String(40))
    model: Mapped[str] = mapped_column(String(100))
    purpose: Mapped[str] = mapped_column(String(60))
    latency_ms: Mapped[int] = mapped_column()
    input_tokens: Mapped[int] = mapped_column(default=0)
    output_tokens: Mapped[int] = mapped_column(default=0)
    estimated_cost_micros: Mapped[int] = mapped_column(default=0)
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    succeeded: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class SimulationSnapshot(Base):
    __tablename__ = "simulation_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "world_id", "event_sequence", name="uq_simulation_snapshots_world_sequence"
        ),
        CheckConstraint("event_sequence >= 0", name="ck_simulation_snapshots_sequence"),
        Index("ix_simulation_snapshots_world_date", "world_id", "simulation_date"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    world_id: Mapped[UUID] = mapped_column(ForeignKey("worlds.id", ondelete="CASCADE"), index=True)
    event_sequence: Mapped[int] = mapped_column(BigInteger)
    simulation_date: Mapped[date] = mapped_column(Date)
    schema_version: Mapped[int] = mapped_column(default=1)
    engine_version: Mapped[str] = mapped_column(String(32))
    rng_state: Mapped[dict[str, Any]] = mapped_column(JSON)
    state: Mapped[dict[str, Any]] = mapped_column(JSON)
    checksum: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class WorldMetric(Base):
    __tablename__ = "world_metrics"
    __table_args__ = (
        UniqueConstraint(
            "world_id",
            "simulation_date",
            "name",
            "scope",
            "entity_id",
            name="uq_world_metrics_point",
        ),
        Index("ix_world_metrics_world_name_date", "world_id", "name", "simulation_date"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    world_id: Mapped[UUID] = mapped_column(ForeignKey("worlds.id", ondelete="CASCADE"), index=True)
    simulation_date: Mapped[date] = mapped_column(Date)
    name: Mapped[str] = mapped_column(String(80))
    scope: Mapped[str] = mapped_column(String(20), default="world")
    entity_id: Mapped[UUID] = mapped_column(Uuid)
    value: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    unit: Mapped[str] = mapped_column(String(32))
    labels: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
