import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

from genesis_simulation.model import JsonValue


@dataclass(frozen=True, slots=True)
class StreamMessage:
    sequence: int
    channel: str
    data: dict[str, JsonValue]


@dataclass(slots=True)
class StreamBroker:
    """Bounded changed-data stream with explicit slow-consumer recovery."""

    queue_size: int = 100
    _sequence: int = 0
    _clients: dict[str, tuple[frozenset[str], asyncio.Queue[StreamMessage]]] = field(
        default_factory=dict
    )

    def connect(self, client_id: str, channels: frozenset[str]) -> asyncio.Queue[StreamMessage]:
        if not client_id or not channels:
            raise ValueError("client_id and at least one channel are required")
        queue: asyncio.Queue[StreamMessage] = asyncio.Queue(maxsize=self.queue_size)
        self._clients[client_id] = (channels, queue)
        return queue

    def disconnect(self, client_id: str) -> None:
        self._clients.pop(client_id, None)

    def publish(self, channel: str, data: dict[str, JsonValue]) -> StreamMessage:
        self._sequence += 1
        message = StreamMessage(self._sequence, channel, data)
        disconnected: list[str] = []
        for client_id, (channels, queue) in self._clients.items():
            if channel not in channels:
                continue
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                disconnected.append(client_id)
        for client_id in disconnected:
            self.disconnect(client_id)
        return message

    async def messages(
        self, client_id: str, channels: frozenset[str], *, heartbeat_seconds: float = 15.0
    ) -> AsyncIterator[StreamMessage | None]:
        queue = self.connect(client_id, channels)
        try:
            while client_id in self._clients:
                try:
                    yield await asyncio.wait_for(queue.get(), timeout=heartbeat_seconds)
                except TimeoutError:
                    yield None
        finally:
            self.disconnect(client_id)
