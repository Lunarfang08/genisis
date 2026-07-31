from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class Party:
    party_id: str
    name: str
    ideology: int


@dataclass(frozen=True, slots=True)
class Candidate:
    citizen_id: str
    party_id: str
    competence: int
    reputation: int


@dataclass(frozen=True, slots=True)
class Voter:
    citizen_id: str
    ideology: int
    income_minor: int
    employed: bool
    education: int
    happiness: int
    government_approval: int
    social_influence: int = 0
    recent_event_sentiment: int = 0


@dataclass(frozen=True, slots=True)
class ElectionResult:
    held_on: date
    winner_citizen_id: str
    votes: dict[str, int]
    turnout: int


def run_election(
    held_on: date,
    parties: tuple[Party, ...],
    candidates: tuple[Candidate, ...],
    voters: tuple[Voter, ...],
) -> ElectionResult:
    """Resolve an election without randomness or provider output."""

    party_by_id = {party.party_id: party for party in parties}
    if not candidates or any(item.party_id not in party_by_id for item in candidates):
        raise ValueError("every election needs candidates belonging to known parties")
    votes = {candidate.citizen_id: 0 for candidate in candidates}
    for voter in sorted(voters, key=lambda item: item.citizen_id):
        scored: list[tuple[int, str, Candidate]] = []
        for candidate in candidates:
            party = party_by_id[candidate.party_id]
            ideology_fit = 100 - min(100, abs(voter.ideology - party.ideology))
            economic_confidence = voter.government_approval + (10 if voter.employed else -10)
            wellbeing = (voter.happiness + voter.education) // 2
            value = (
                ideology_fit * 4
                + candidate.competence * 2
                + candidate.reputation
                + economic_confidence
                + wellbeing
                + voter.social_influence
                + voter.recent_event_sentiment
            )
            scored.append((value, candidate.citizen_id, candidate))
        selected = max(scored)[2]
        votes[selected.citizen_id] += 1
    winner = max(sorted(votes), key=lambda candidate_id: votes[candidate_id])
    return ElectionResult(held_on, winner, votes, len(voters))


@dataclass(slots=True)
class PublicPolicy:
    code: str
    tax_percent: int
    service_spending_percent: int
    happiness_effect: int
    active: bool = False

    def enact(self, treasury_minor: int) -> tuple[int, int]:
        if not 0 <= self.tax_percent <= 100:
            raise ValueError("tax_percent must be between 0 and 100")
        if not 0 <= self.service_spending_percent <= 100:
            raise ValueError("service_spending_percent must be between 0 and 100")
        self.active = True
        spending = treasury_minor * self.service_spending_percent // 100
        return treasury_minor - spending, self.happiness_effect
