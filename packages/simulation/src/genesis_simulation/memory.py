from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum


class MemoryType(StrEnum):
    PERSONAL = "personal_event"
    RELATIONSHIP = "relationship_event"
    CAREER = "career_event"
    POLITICAL = "political_event"
    TRAUMATIC = "traumatic_event"
    ACHIEVEMENT = "achievement"
    FAILURE = "failure"
    BELIEF_CHANGING = "belief_changing_event"


@dataclass(slots=True)
class Memory:
    memory_id: str
    type: MemoryType
    occurred_on: date
    importance: int
    emotional_score: int
    related_citizens: tuple[str, ...] = ()
    related_event_id: str | None = None
    decay_basis_points: int = 100
    recall_score: int = 100
    consolidated: bool = False

    def __post_init__(self) -> None:
        if not 0 <= self.importance <= 100:
            raise ValueError("importance must be between 0 and 100")
        if not -100 <= self.emotional_score <= 100:
            raise ValueError("emotional_score must be between -100 and 100")
        if not 0 <= self.decay_basis_points <= 10_000:
            raise ValueError("decay_basis_points must be between 0 and 10000")


@dataclass(slots=True)
class Goal:
    goal_id: str
    title: str
    priority: int
    progress: int = 0
    status: str = "active"

    def advance(self, amount: int) -> str:
        if self.status != "active":
            return self.status
        self.progress = max(0, min(100, self.progress + amount))
        if self.progress == 100:
            self.status = "completed"
        return self.status

    def fail(self) -> None:
        if self.status == "active":
            self.status = "failed"


@dataclass(slots=True)
class CitizenMind:
    short_term_limit: int = 20
    memories: list[Memory] = field(default_factory=list)
    goals: list[Goal] = field(default_factory=list)

    def remember(self, memory: Memory) -> None:
        self.memories.append(memory)
        self.memories.sort(key=lambda item: (item.occurred_on, item.memory_id))
        short_term = [item for item in self.memories if not item.consolidated]
        overflow = len(short_term) - self.short_term_limit
        if overflow > 0:
            candidates = sorted(short_term, key=lambda item: (item.importance, item.memory_id))
            for item in candidates[:overflow]:
                if item.importance >= 70:
                    item.consolidated = True
                else:
                    self.memories.remove(item)

    def decay(self, days: int) -> None:
        if days < 0:
            raise ValueError("days cannot be negative")
        for memory in self.memories:
            protected = memory.importance >= 85 or memory.consolidated
            loss = 0 if protected else memory.decay_basis_points * days // 10_000
            memory.recall_score = max(0, memory.recall_score - loss)
        self.memories = [
            memory for memory in self.memories if memory.recall_score > 0 or memory.importance >= 85
        ]

    def recall(self, *, related_citizen: str | None = None, limit: int = 5) -> tuple[Memory, ...]:
        if not 1 <= limit <= 20:
            raise ValueError("limit must be between 1 and 20")
        candidates = [
            memory
            for memory in self.memories
            if related_citizen is None or related_citizen in memory.related_citizens
        ]
        candidates.sort(
            key=lambda item: (
                item.importance * item.recall_score,
                abs(item.emotional_score),
                item.occurred_on,
                item.memory_id,
            ),
            reverse=True,
        )
        return tuple(candidates[:limit])

    def decision_bias(self, related_citizen: str | None = None) -> int:
        recalled = self.recall(related_citizen=related_citizen)
        if not recalled:
            return 0
        weighted = sum(
            item.emotional_score * item.importance * item.recall_score for item in recalled
        )
        denominator = sum(item.importance * item.recall_score for item in recalled)
        return weighted // denominator if denominator else 0

    def replace_failed_goal(self, replacement: Goal) -> None:
        failed = sorted(
            (goal for goal in self.goals if goal.status == "failed"),
            key=lambda goal: (-goal.priority, goal.goal_id),
        )
        if failed:
            failed[0].status = "replaced"
        self.goals.append(replacement)
