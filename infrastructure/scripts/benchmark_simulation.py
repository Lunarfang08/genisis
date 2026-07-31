"""Repeatable GENESIS engine benchmark; run from the repository root."""

import argparse
import json
import statistics
import sys
import time
import tracemalloc
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "simulation" / "src"))

from genesis_simulation.engine import SimulationEngine  # noqa: E402
from genesis_simulation.model import CitizenState, EngineConfig, WorldState  # noqa: E402


def benchmark(count: int, ticks: int) -> dict[str, float | int]:
    citizens = {
        f"{index:032x}": CitizenState(
            id=f"{index:032x}",
            birth_date=date(1980 + index % 35, 1 + index % 12, 1 + index % 27),
            employment_status="employed" if index % 3 else "unemployed",
            occupation="worker" if index % 3 else None,
            wealth_minor=10_000 + index % 50_000,
        )
        for index in range(count)
    }
    state = WorldState(
        world_id="00000000-0000-0000-0000-000000000001",
        seed=42,
        simulation_date=date(2200, 1, 1),
        citizens=citizens,
    )
    engine = SimulationEngine(state, config=EngineConfig(snapshot_interval=0))
    tracemalloc.start()
    durations = []
    for _ in range(ticks):
        started = time.perf_counter()
        engine.run_ticks(1)
        durations.append((time.perf_counter() - started) * 1_000)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "citizens": count,
        "ticks": ticks,
        "median_tick_ms": round(statistics.median(durations), 2),
        "p95_tick_ms": round(sorted(durations)[max(0, round(len(durations) * 0.95) - 1)], 2),
        "peak_memory_mb": round(peak / 1_048_576, 2),
        "events": len(engine.events),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--citizens", type=int, nargs="+", default=[1_000, 10_000, 50_000])
    parser.add_argument("--ticks", type=int, default=3)
    arguments = parser.parse_args()
    print(json.dumps([benchmark(count, arguments.ticks) for count in arguments.citizens], indent=2))


if __name__ == "__main__":
    main()
