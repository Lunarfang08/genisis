from datetime import date

from genesis_simulation.model import CitizenState, WorldState

WORLD_ID = "11111111-1111-1111-1111-111111111111"
CITIZEN_A = "22222222-2222-2222-2222-222222222222"
CITIZEN_B = "33333333-3333-3333-3333-333333333333"


def world_state_factory(*, seed: int = 42, reverse_citizens: bool = False) -> WorldState:
    citizens = [
        CitizenState(
            id=CITIZEN_A,
            birth_date=date(2170, 6, 12),
            health=85,
            happiness=65,
            employment_status="employed",
            occupation="engineer",
            wealth_minor=1_000,
        ),
        CitizenState(
            id=CITIZEN_B,
            birth_date=date(2183, 1, 1),
            lifecycle_status="child",
            health=92,
            happiness=72,
            employment_status="unemployed",
            wealth_minor=500,
        ),
    ]
    if reverse_citizens:
        citizens.reverse()
    return WorldState(
        world_id=WORLD_ID,
        seed=seed,
        simulation_date=date(2200, 12, 30),
        citizens={citizen.id: citizen for citizen in citizens},
    )
