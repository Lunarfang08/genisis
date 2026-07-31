"use client";

import type { ControlResponse } from "@/lib/shared-types";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { apiRequest } from "@/lib/browser-api";

const commands = [
  ["resume", "Run"],
  ["pause", "Pause"],
  ["step", "Step"],
  ["reset", "Reset"],
] as const;

export function SimulationControls({
  worldId,
  initialSpeed,
}: {
  worldId: string;
  initialSpeed: number;
}) {
  const router = useRouter();
  const [speed, setSpeed] = useState(initialSpeed);
  const [status, setStatus] = useState("CONTROL LINK READY");
  const [busy, setBusy] = useState(false);

  async function send(command: string, extra: Record<string, unknown> = {}) {
    setBusy(true);
    try {
      const response = await apiRequest<ControlResponse>(
        `/worlds/${worldId}/controls`,
        {
          method: "POST",
          body: JSON.stringify({ command, ...extra }),
        },
      );
      setStatus(
        `${response.command.toUpperCase()} ACCEPTED · #${response.sequence}`,
      );
      router.refresh();
      window.setTimeout(() => router.refresh(), 1_200);
    } catch (cause) {
      setStatus(cause instanceof Error ? cause.message : "CONTROL FAILED");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="simulation-controls" aria-label="Simulation controls">
      <div>
        <span className="eyebrow">LIVE CONTROL PLANE</span>
        <strong>{status}</strong>
      </div>
      <div className="control-buttons">
        {commands.map(([command, label]) => (
          <button
            disabled={busy}
            key={command}
            onClick={() => void send(command)}
            type="button"
          >
            {label}
          </button>
        ))}
        <label>
          <span>Speed</span>
          <select
            disabled={busy}
            onChange={(event) => {
              const value = Number(event.target.value);
              setSpeed(value);
              void send("set_speed", { speed: value });
            }}
            value={speed}
          >
            {[1, 2, 4, 8, 12, 30, 60].map((value) => (
              <option key={value} value={value}>
                {value}×
              </option>
            ))}
          </select>
        </label>
      </div>
    </section>
  );
}
