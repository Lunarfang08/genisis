from dataclasses import dataclass


@dataclass(slots=True)
class EconomicCitizen:
    citizen_id: str
    household_id: str
    employed: bool
    salary_minor: int
    wealth_minor: int


@dataclass(slots=True)
class BusinessAccount:
    business_id: str
    industry: str
    cash_minor: int
    employees: int
    unit_price_minor: int
    demand_units: int
    operating_cost_minor: int
    active: bool = True


@dataclass(frozen=True, slots=True)
class EconomyConfig:
    tax_percent: int = 10
    household_consumption_percent: int = 60
    inflation_basis_points: int = 20
    bankruptcy_floor_minor: int = 0

    def __post_init__(self) -> None:
        for name in ("tax_percent", "household_consumption_percent"):
            if not 0 <= getattr(self, name) <= 100:
                raise ValueError(f"{name} must be between 0 and 100")
        if not -1_000 <= self.inflation_basis_points <= 10_000:
            raise ValueError("inflation_basis_points is outside the supported range")


@dataclass(frozen=True, slots=True)
class EconomyMetrics:
    gdp_minor: int
    tax_revenue_minor: int
    household_income_minor: int
    household_consumption_minor: int
    business_profit_minor: int
    employed: int
    unemployed: int
    average_salary_minor: int
    inflation_basis_points: int
    business_closures: int


def simulate_economy(
    citizens: list[EconomicCitizen],
    businesses: list[BusinessAccount],
    config: EconomyConfig | None = None,
) -> EconomyMetrics:
    """Settle one period using integer-only, documented accounting formulas."""

    config = config or EconomyConfig()
    income = sum(item.salary_minor for item in citizens if item.employed)
    tax = income * config.tax_percent // 100
    consumption_budget = income * config.household_consumption_percent // 100
    employed = sum(item.employed for item in citizens)
    unemployed = len(citizens) - employed

    for citizen in sorted(citizens, key=lambda item: item.citizen_id):
        earned = citizen.salary_minor if citizen.employed else 0
        citizen_tax = earned * config.tax_percent // 100
        citizen_consumption = earned * config.household_consumption_percent // 100
        citizen.wealth_minor = max(
            0, citizen.wealth_minor + earned - citizen_tax - citizen_consumption
        )

    revenue_total = 0
    profit_total = 0
    closures = 0
    active = [business for business in businesses if business.active]
    total_demand = sum(max(0, business.demand_units) for business in active)
    for business in sorted(active, key=lambda item: item.business_id):
        demand_share = (
            consumption_budget * max(0, business.demand_units) // total_demand
            if total_demand
            else 0
        )
        price_adjustment = business.unit_price_minor * config.inflation_basis_points // 10_000
        business.unit_price_minor = max(1, business.unit_price_minor + price_adjustment)
        revenue = demand_share
        profit = revenue - business.operating_cost_minor
        business.cash_minor += profit
        revenue_total += revenue
        profit_total += profit
        if business.cash_minor < config.bankruptcy_floor_minor:
            business.cash_minor = 0
            business.active = False
            closures += 1

    average_salary = income // employed if employed else 0
    return EconomyMetrics(
        gdp_minor=income + revenue_total,
        tax_revenue_minor=tax,
        household_income_minor=income,
        household_consumption_minor=consumption_budget,
        business_profit_minor=profit_total,
        employed=employed,
        unemployed=unemployed,
        average_salary_minor=average_salary,
        inflation_basis_points=config.inflation_basis_points,
        business_closures=closures,
    )
