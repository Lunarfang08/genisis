import json
from time import perf_counter
from typing import Any, cast
from uuid import UUID

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from genesis_api.core.settings import Settings
from genesis_api.db.models import AIUsage, SimulationEvent, WorldSettings
from genesis_api.repositories.history import CommittedEvent, EventRepository


class NarrativeService:
    """Adds optional prose to facts after deterministic events are committed."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def annotate_next(self, session: AsyncSession) -> bool:
        if not self.settings.ai_enabled:
            return False
        world_settings = (
            await session.scalars(
                select(WorldSettings).where(WorldSettings.scenario_config.is_not(None))
            )
        ).all()
        for settings in world_settings:
            config = settings.scenario_config
            if not bool(config.get("ai_enabled", False)):
                continue
            event = await self._next_event(session, settings.world_id)
            if event is None:
                continue
            calls_today = await session.scalar(
                select(func.count(AIUsage.id)).where(
                    AIUsage.world_id == settings.world_id,
                    AIUsage.simulation_date == event.simulation_date,
                )
            )
            if int(calls_today or 0) >= self.settings.ai_daily_call_budget:
                continue
            provider = str(config.get("ai_provider", self.settings.ai_provider))
            await self._annotate(session, settings, event, provider)
            return True
        return False

    async def _next_event(self, session: AsyncSession, world_id: UUID) -> SimulationEvent | None:
        candidates = (
            await session.scalars(
                select(SimulationEvent)
                .where(
                    SimulationEvent.world_id == world_id,
                    SimulationEvent.importance >= 75,
                    SimulationEvent.category != "ai",
                )
                .order_by(SimulationEvent.sequence)
                .limit(20)
            )
        ).all()
        for event in candidates:
            purpose = f"narrative:{event.id}"
            used = await session.scalar(select(AIUsage.id).where(AIUsage.purpose == purpose))
            if used is None:
                return event
        return None

    async def _annotate(
        self,
        session: AsyncSession,
        settings: WorldSettings,
        event: SimulationEvent,
        provider: str,
    ) -> None:
        started = perf_counter()
        succeeded = True
        input_tokens = 0
        output_tokens = 0
        model = self.settings.ai_model
        try:
            if provider == "groq":
                title, text, input_tokens, output_tokens = await self._groq(event)
            else:
                provider = "mock"
                model = "deterministic-mock-v1"
                title = event.event_type.replace(".", " ").title()
                text = (
                    f"On {event.simulation_date.isoformat()}, the civilization recorded "
                    f"{event.event_type.replace('.', ' ')}."
                )
        except Exception:
            succeeded = False
            title = "Narrative unavailable"
            text = "The deterministic event remains available in the verified timeline."
        latency_ms = round((perf_counter() - started) * 1_000)
        session.add(
            AIUsage(
                world_id=settings.world_id,
                simulation_date=event.simulation_date,
                provider=provider,
                model=model,
                purpose=f"narrative:{event.id}",
                latency_ms=latency_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                succeeded=succeeded,
            )
        )
        await EventRepository(session).append(
            settings.world_id,
            (
                CommittedEvent(
                    simulation_date=event.simulation_date,
                    category="ai",
                    event_type="ai.narrative_generated",
                    payload={
                        "source_event_id": str(event.id),
                        "title": title,
                        "text": text,
                        "provider": provider,
                        "model": model,
                        "fallback": not succeeded,
                    },
                    engine_version=event.engine_version,
                    causation_id=event.id,
                    correlation_id=event.correlation_id,
                    severity="info" if succeeded else "notice",
                    importance=max(10, event.importance - 20),
                ),
            ),
        )
        await session.commit()

    async def _groq(self, event: SimulationEvent) -> tuple[str, str, int, int]:
        if not self.settings.groq_api_key:
            raise RuntimeError("Groq API key is not configured")
        prompt = (
            "Write a concise fictional historical note about this deterministic simulation "
            "event. Do not invent statistics, people, causes, or outcomes. Return JSON with "
            f"string fields title and text only. Event: {event.event_type}; "
            f"date: {event.simulation_date.isoformat()}; facts: "
            f"{json.dumps(event.payload, sort_keys=True)}"
        )
        async with httpx.AsyncClient(timeout=self.settings.ai_timeout_seconds) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.settings.groq_api_key}"},
                json={
                    "model": self.settings.ai_model,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You narrate verified fictional simulation events. "
                                "Never change or add facts."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.2,
                    "max_completion_tokens": 220,
                    "response_format": {"type": "json_object"},
                },
            )
            response.raise_for_status()
        body = cast(dict[str, Any], response.json())
        content = str(body["choices"][0]["message"]["content"])
        parsed = cast(dict[str, Any], json.loads(content))
        title = str(parsed.get("title", "Historical note"))[:160]
        text = str(parsed.get("text", ""))[:2_000]
        if not text:
            raise ValueError("Groq returned an empty narrative")
        usage = cast(dict[str, Any], body.get("usage", {}))
        return (
            title,
            text,
            int(usage.get("prompt_tokens", 0)),
            int(usage.get("completion_tokens", 0)),
        )
