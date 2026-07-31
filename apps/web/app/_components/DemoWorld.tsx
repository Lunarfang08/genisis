"use client";

import { useMemo, useState } from "react";

function value(
  seed: number,
  day: number,
  salt: number,
  base: number,
  spread: number,
) {
  const x = Math.sin(seed * 12.9898 + day * 78.233 + salt) * 43758.5453;
  return Math.round(base + (x - Math.floor(x)) * spread);
}

export function DemoWorld() {
  const [seed, setSeed] = useState(42);
  const [day, setDay] = useState(0);
  const metrics = useMemo(
    () => ({
      population: 1200 + day * 3 + value(seed, day, 1, -8, 16),
      gdp: 4_200_000 + day * 18_500 + value(seed, day, 2, -9_000, 18_000),
      happiness: value(seed, day, 3, 58, 24),
      approval: value(seed, day, 4, 44, 36),
    }),
    [seed, day],
  );
  return (
    <div className="demo-console">
      <div className="demo-controls">
        <label>
          World seed
          <input
            type="number"
            min="0"
            max="2147483647"
            value={seed}
            onChange={(event) => {
              setSeed(Number(event.target.value));
              setDay(0);
            }}
          />
        </label>
        <button onClick={() => setDay((value) => value + 1)}>
          Single-step day
        </button>
        <button onClick={() => setDay((value) => value + 30)}>
          Advance month
        </button>
        <button onClick={() => setDay(0)}>Reset seed</button>
      </div>
      <div className="demo-date">
        <span>SIMULATION DATE</span>
        <strong>YEAR 1 · DAY {day + 1}</strong>
        <small>Same seed + commands always produce the same readout.</small>
      </div>
      <section className="dashboard-kpis">
        {Object.entries(metrics).map(([name, metric]) => (
          <article key={name}>
            <span>{name}</span>
            <strong>{metric.toLocaleString()}</strong>
          </article>
        ))}
      </section>
      <div
        className="demo-world-grid"
        aria-label="Interactive deterministic demo visualization"
      >
        {Array.from({ length: 18 }, (_, index) => (
          <i
            key={index}
            style={{
              left: `${value(seed, day, index, 4, 90)}%`,
              top: `${value(seed, day, index + 100, 6, 82)}%`,
              opacity: value(seed, day, index + 200, 35, 65) / 100,
            }}
          />
        ))}
      </div>
      <p className="demo-disclosure">
        This browser-only demonstration uses a transparent seeded formula and
        makes no API or paid AI calls. Private worlds use the full deterministic
        engine and durable event history.
      </p>
    </div>
  );
}
