from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol

from genesis_simulation.model import JsonValue


@dataclass(frozen=True, slots=True)
class GenerationRequest:
    purpose: str
    prompt: str
    schema: dict[str, JsonValue]
    max_tokens: int = 300


@dataclass(frozen=True, slots=True)
class GenerationResult:
    content: dict[str, JsonValue]
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cached: bool = False


class AIProvider(Protocol):
    name: str

    def generate(self, request: GenerationRequest) -> GenerationResult: ...


@dataclass(slots=True)
class MockProvider:
    responses: dict[str, dict[str, JsonValue]]
    name: str = "mock"
    model: str = "deterministic-mock-v1"
    calls: int = 0

    def generate(self, request: GenerationRequest) -> GenerationResult:
        self.calls += 1
        content = self.responses.get(
            request.purpose,
            {"title": "Historical note", "text": "No narrative was configured."},
        )
        return GenerationResult(
            content=content,
            provider=self.name,
            model=self.model,
            input_tokens=max(1, len(request.prompt.split())),
            output_tokens=max(1, len(str(content).split())),
        )


@dataclass(slots=True)
class CircuitBreaker:
    failure_threshold: int = 3
    failures: int = 0
    open: bool = False

    def record_success(self) -> None:
        self.failures = 0
        self.open = False

    def record_failure(self) -> None:
        self.failures += 1
        self.open = self.failures >= self.failure_threshold


Validator = Callable[[dict[str, JsonValue]], bool]


@dataclass(slots=True)
class AIService:
    providers: dict[str, AIProvider]
    primary: str
    fallback: str | None = None
    enabled: bool = False
    daily_call_budget: int = 5
    breaker: CircuitBreaker = field(default_factory=CircuitBreaker)
    _cache: dict[str, GenerationResult] = field(default_factory=dict)
    _daily_calls: dict[str, int] = field(default_factory=dict)

    def generate(
        self,
        *,
        simulation_day: str,
        cache_key: str,
        request: GenerationRequest,
        validator: Validator,
    ) -> GenerationResult:
        cached = self._cache.get(cache_key)
        if cached is not None:
            return GenerationResult(
                content=cached.content,
                provider=cached.provider,
                model=cached.model,
                input_tokens=cached.input_tokens,
                output_tokens=cached.output_tokens,
                cached=True,
            )
        if not self.enabled:
            raise RuntimeError("AI features are disabled")
        calls = self._daily_calls.get(simulation_day, 0)
        if calls >= self.daily_call_budget:
            raise RuntimeError("daily AI call budget exhausted")
        provider_names = (self.primary, self.fallback)
        last_error: Exception | None = None
        for name in provider_names:
            if name is None or name not in self.providers:
                continue
            if name == self.primary and self.breaker.open:
                continue
            try:
                result = self.providers[name].generate(request)
                if not validator(result.content):
                    raise ValueError("provider returned invalid structured output")
                self.breaker.record_success()
                self._daily_calls[simulation_day] = calls + 1
                self._cache[cache_key] = result
                return result
            except Exception as exc:
                last_error = exc
                if name == self.primary:
                    self.breaker.record_failure()
        raise RuntimeError("all AI providers failed") from last_error


def major_event_eligible(importance: int, category: str) -> bool:
    return importance >= 75 and category in {
        "government",
        "disaster",
        "science",
        "business",
        "history",
    }
