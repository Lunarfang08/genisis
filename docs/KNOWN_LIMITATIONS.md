# Known limitations

- One civilization and one active deterministic writer per world; diplomacy, conflict, modding, technology progression, and newspapers remain optional roadmap work.
- The 2D view uses city points and aggregated activity, not GIS terrain or 3D rendering. City detail currently reuses the world observatory with a selected-city context.
- Compare mode supports dates, cities, citizens, policies, and snapshot/run
  checkpoints. Rich causal attribution still needs larger persisted cohorts.
- The worker hydrates and persists complete deterministic world state under a
  single-writer Redis lease. Very large worlds still require horizontal read
  scaling and benchmark-driven worker sizing.
- Performance varies with hardware and database latency. The repository provides load profiles but makes no one-million-citizen claim.
- The development admin surface is aggregate-only and disabled in production; connect a production metrics/error backend for hosted operation.
- No file upload, social login, billing, multiplayer editing, or production email delivery is included.
