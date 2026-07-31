# Performance benchmark

Run: 2026-07-31 on the local Windows verification environment, Python 3.13.14,
8 logical processors (Intel64 family 6 model 140), one deterministic tick,
snapshot creation disabled. Memory is Python allocation peak from `tracemalloc`;
it excludes interpreter, database, and frontend processes.

| Citizens | Tick time | Python allocation peak | Events |
|---:|---:|---:|---:|
| 1,000 | 236.89 ms | 1.72 MB | 1,002 |
| 10,000 | 3,437.11 ms | 17.86 MB | 10,002 |
| 50,000 | 41,943.39 ms | 94.16 MB | 50,002 |

These are single-sample capacity observations, not latency guarantees. A second
two-tick 1,000-citizen run recorded 338.85 ms median and 409.23 ms maximum.
At 10,000 citizens, use a background worker. At 50,000, a dedicated worker and
long tick interval are required on comparable hardware; the current pure-Python
systems are not interactive at that scale. Run the benchmark repeatedly on the
deployment target before selecting population caps.

```bash
python infrastructure/scripts/benchmark_simulation.py --citizens 1000 10000 50000 --ticks 3
```
