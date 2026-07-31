from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from genesis_simulation.randomness import DeterministicRandom


class Season(StrEnum):
    WINTER = "winter"
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"


class DisasterType(StrEnum):
    FIRE = "fire"
    FLOOD = "flood"
    DROUGHT = "drought"
    DISEASE = "disease"


@dataclass(frozen=True, slots=True)
class EnvironmentConfig:
    disaster_frequency_per_10k: int = 10
    disease_frequency_per_10k: int = 6
    pollution_recovery: int = 1

    def __post_init__(self) -> None:
        for value in (self.disaster_frequency_per_10k, self.disease_frequency_per_10k):
            if not 0 <= value <= 10_000:
                raise ValueError("event frequency must be between 0 and 10000")


@dataclass(slots=True)
class EnvironmentState:
    resource_availability: int = 80
    food_supply: int = 80
    pollution: int = 10
    infrastructure: int = 100
    disease_prevalence: int = 0


@dataclass(frozen=True, slots=True)
class EnvironmentalImpact:
    season: Season
    weather: str
    disasters: tuple[DisasterType, ...]
    health_delta: int
    happiness_delta: int
    business_activity_percent: int
    government_cost_minor: int
    migration_pressure: int
    resource_price_basis_points: int


def simulate_environment(
    on_date: date,
    state: EnvironmentState,
    random: DeterministicRandom,
    config: EnvironmentConfig | None = None,
) -> EnvironmentalImpact:
    config = config or EnvironmentConfig()
    season = {
        12: Season.WINTER,
        1: Season.WINTER,
        2: Season.WINTER,
        3: Season.SPRING,
        4: Season.SPRING,
        5: Season.SPRING,
        6: Season.SUMMER,
        7: Season.SUMMER,
        8: Season.SUMMER,
        9: Season.AUTUMN,
        10: Season.AUTUMN,
        11: Season.AUTUMN,
    }[on_date.month]
    weather = {
        Season.WINTER: "cold",
        Season.SPRING: "mild",
        Season.SUMMER: "hot",
        Season.AUTUMN: "windy",
    }[season]
    disasters: list[DisasterType] = []
    if random.randint(1, 10_000) <= config.disaster_frequency_per_10k:
        candidates = (DisasterType.FIRE, DisasterType.FLOOD, DisasterType.DROUGHT)
        disasters.append(candidates[random.randint(0, len(candidates) - 1)])
    if random.randint(1, 10_000) <= config.disease_frequency_per_10k:
        disasters.append(DisasterType.DISEASE)

    state.pollution = max(0, state.pollution - config.pollution_recovery)
    state.resource_availability = max(0, state.resource_availability - len(disasters) * 4)
    state.food_supply = max(0, state.food_supply - len(disasters) * 5)
    state.infrastructure = max(0, state.infrastructure - len(disasters) * 3)
    state.disease_prevalence = min(
        100,
        max(0, state.disease_prevalence - 1) + (10 if DisasterType.DISEASE in disasters else 0),
    )
    severity = len(disasters)
    return EnvironmentalImpact(
        season=season,
        weather=weather,
        disasters=tuple(disasters),
        health_delta=-(severity + state.disease_prevalence // 20),
        happiness_delta=-severity * 2,
        business_activity_percent=max(0, 100 - severity * 10),
        government_cost_minor=severity * 10_000,
        migration_pressure=severity * 5,
        resource_price_basis_points=severity * 250,
    )
