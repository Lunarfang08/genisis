import asyncio
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class LiveUpdate:
    sequence: int
    channel: str
    data: dict[str, Any]


@dataclass(slots=True)
class StreamHub:
    queue_size: int = 100
    _subscribers: dict[str, tuple[str, frozenset[str], asyncio.Queue[LiveUpdate]]] = field(
        default_factory=dict
    )

    def subscribe(
        self, client_id: str, world_id: str, channels: frozenset[str]
    ) -> asyncio.Queue[LiveUpdate]:
        queue: asyncio.Queue[LiveUpdate] = asyncio.Queue(maxsize=self.queue_size)
        self._subscribers[client_id] = (world_id, channels, queue)
        return queue

    @property
    def connection_count(self) -> int:
        return len(self._subscribers)

    def unsubscribe(self, client_id: str) -> None:
        self._subscribers.pop(client_id, None)

    def publish(self, world_id: str, update: LiveUpdate) -> None:
        slow_clients: list[str] = []
        for client_id, (subscribed_world, channels, queue) in self._subscribers.items():
            if subscribed_world != world_id or update.channel not in channels:
                continue
            try:
                queue.put_nowait(update)
            except asyncio.QueueFull:
                slow_clients.append(client_id)
        for client_id in slow_clients:
            self.unsubscribe(client_id)
