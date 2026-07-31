import hashlib
import json

from genesis_simulation.errors import SnapshotIntegrityError
from genesis_simulation.model import JsonValue, SimulationSnapshot, WorldState
from genesis_simulation.randomness import DeterministicRandom


def _checksum(
    *,
    engine_version: str,
    system_manifest: tuple[str, ...],
    state: dict[str, JsonValue],
) -> str:
    serialized = json.dumps(
        {
            "engine_version": engine_version,
            "system_manifest": system_manifest,
            "state": state,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(serialized.encode()).hexdigest()


def create_snapshot(
    state: WorldState, *, engine_version: str, system_manifest: tuple[str, ...]
) -> SimulationSnapshot:
    serialized_state = state.to_dict()
    return SimulationSnapshot(
        world_id=state.world_id,
        tick=state.tick,
        event_sequence=state.event_sequence,
        engine_version=engine_version,
        rng_algorithm=DeterministicRandom.algorithm,
        rng_version=DeterministicRandom.version,
        system_manifest=system_manifest,
        state=serialized_state,
        checksum=_checksum(
            engine_version=engine_version,
            system_manifest=system_manifest,
            state=serialized_state,
        ),
    )


def restore_snapshot(
    snapshot: SimulationSnapshot,
    *,
    expected_engine_version: str,
    expected_system_manifest: tuple[str, ...],
) -> WorldState:
    if snapshot.engine_version != expected_engine_version:
        raise SnapshotIntegrityError("snapshot engine version is incompatible")
    if snapshot.system_manifest != expected_system_manifest:
        raise SnapshotIntegrityError("snapshot system order is incompatible")
    actual = _checksum(
        engine_version=snapshot.engine_version,
        system_manifest=snapshot.system_manifest,
        state=snapshot.state,
    )
    if actual != snapshot.checksum:
        raise SnapshotIntegrityError("snapshot checksum is invalid")
    if snapshot.rng_algorithm != DeterministicRandom.algorithm:
        raise SnapshotIntegrityError("snapshot RNG algorithm is incompatible")
    if snapshot.rng_version != DeterministicRandom.version:
        raise SnapshotIntegrityError("snapshot RNG version is incompatible")
    return WorldState.from_dict(snapshot.state)
