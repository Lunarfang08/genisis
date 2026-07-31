"use client";

import type { User, World } from "@/lib/shared-types";
import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import { Toast } from "@/app/_components/Toast";
import { apiRequest } from "@/lib/browser-api";
import { formatIsoDate } from "@/lib/format";

export function WorkspaceClient({
  user,
  initialWorlds,
  initialNotice,
}: {
  user: User;
  initialWorlds: World[];
  initialNotice: string;
}) {
  const [worlds, setWorlds] = useState<World[]>(initialWorlds);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState(initialNotice);
  const [population, setPopulation] = useState(1_000);

  useEffect(() => {
    if (!initialNotice) return;

    window.history.replaceState(null, "", "/workspace");
    const timeout = window.setTimeout(() => setNotice(""), 5_000);
    return () => window.clearTimeout(timeout);
  }, [initialNotice]);

  async function loadWorlds() {
    try {
      const response = await apiRequest<{ items: World[] }>("/worlds");
      setWorlds(response.items);
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Worlds could not be loaded.",
      );
    }
  }

  async function createWorld(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const form = event.currentTarget;
    const data = new FormData(form);
    try {
      await apiRequest<World>("/worlds", {
        method: "POST",
        body: JSON.stringify({
          name: data.get("name"),
          seed: Number(data.get("seed")),
          tick_rate: Number(data.get("tickRate")),
          initial_population: Number(data.get("population")),
          city_count: Number(data.get("cities")),
          government_type: "democracy",
          economic_difficulty: Number(data.get("economicDifficulty")),
          resource_abundance: Number(data.get("resourceAbundance")),
          disaster_frequency: Number(data.get("disasterFrequency")),
          disease_frequency: Number(data.get("diseaseFrequency")),
          technology_level: Number(data.get("technologyLevel")),
          social_volatility: Number(data.get("socialVolatility")),
          scenario: data.get("scenario"),
          ai_enabled: data.get("aiEnabled") === "on",
          ai_provider: data.get("aiProvider"),
        }),
      });
      form.reset();
      await loadWorlds();
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "World creation failed.",
      );
    }
  }

  async function logout() {
    try {
      await apiRequest<void>("/auth/logout", { method: "POST" });
      window.location.assign("/login");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Sign out failed.");
    }
  }

  return (
    <div className="workspace-page">
      {notice && <Toast message={notice} onDismiss={() => setNotice("")} />}
      <header className="workspace-topbar">
        <Link className="brand" href="/">
          <span className="brand-mark" aria-hidden="true">
            G
          </span>
          <span>
            <strong>GENESIS</strong>
            <small>observer workspace</small>
          </span>
        </Link>
        <div className="observer-readout">
          <span>AUTHENTICATED OBSERVER</span>
          <strong>{user.display_name}</strong>
        </div>
        <button className="button-secondary" type="button" onClick={logout}>
          Sign out
        </button>
      </header>

      <main className="workspace-main">
        <section className="workspace-heading">
          <div>
            <span className="eyebrow">USER WORKSPACE / WORLD REGISTRY</span>
            <h1>Your worlds.</h1>
            <p>
              Each world is private to your observer identity and begins with an
              immutable seed.
            </p>
          </div>
          <span className="workspace-count">
            {worlds.length.toString().padStart(2, "0")} REGISTERED
          </span>
        </section>

        <section className="workspace-grid">
          <form className="world-create-card" onSubmit={createWorld}>
            <span className="eyebrow">INITIALIZE WORLD</span>
            <h2>Seed a new territory</h2>
            <label>
              World name
              <input
                name="name"
                minLength={2}
                maxLength={80}
                required
                placeholder="Aurora"
              />
            </label>
            <div className="form-pair">
              <label>
                Seed
                <input
                  name="seed"
                  type="number"
                  min="0"
                  max="2147483647"
                  required
                  defaultValue="42"
                />
              </label>
              <label>
                Tick rate
                <input
                  name="tickRate"
                  type="number"
                  min="1"
                  max="60"
                  required
                  defaultValue="1"
                />
              </label>
            </div>
            <label>
              Scenario template
              <select name="scenario" defaultValue="balanced">
                <option value="balanced">Balanced Society</option>
                <option value="economic_crisis">Economic Crisis</option>
                <option value="rapid_growth">Rapid Growth</option>
                <option value="resource_scarcity">Resource Scarcity</option>
                <option value="political_instability">
                  Political Instability
                </option>
                <option value="disaster_prone">Disaster-Prone World</option>
                <option value="high_technology">High-Technology Society</option>
              </select>
            </label>
            <div className="form-pair">
              <label>
                Initial population
                <input
                  name="population"
                  type="number"
                  min="10"
                  max="50000"
                  required
                  value={population}
                  onChange={(event) =>
                    setPopulation(Number(event.target.value))
                  }
                />
              </label>
              <label>
                Cities
                <input
                  name="cities"
                  type="number"
                  min="1"
                  max="50"
                  required
                  defaultValue="3"
                />
              </label>
            </div>
            <details className="advanced-world-settings">
              <summary>Advanced world pressures</summary>
              <div className="pressure-grid">
                {[
                  ["economicDifficulty", "Economic difficulty", 50],
                  ["resourceAbundance", "Resource abundance", 50],
                  ["disasterFrequency", "Disaster frequency", 20],
                  ["diseaseFrequency", "Disease frequency", 20],
                  ["technologyLevel", "Technology level", 30],
                  ["socialVolatility", "Social volatility", 30],
                ].map(([name, label, value]) => (
                  <label key={name as string}>
                    {label}
                    <input
                      name={name as string}
                      type="range"
                      min="0"
                      max="100"
                      defaultValue={value}
                    />
                  </label>
                ))}
              </div>
              <div className="form-pair">
                <label className="checkbox-label">
                  <input name="aiEnabled" type="checkbox" /> Enable optional AI
                  narratives
                </label>
                <label>
                  AI provider
                  <select name="aiProvider" defaultValue="mock">
                    <option value="mock">Deterministic mock</option>
                    <option value="groq">Groq</option>
                    <option value="ollama">Local Ollama</option>
                  </select>
                </label>
              </div>
            </details>
            <aside className="capacity-estimate" aria-live="polite">
              <span>PROJECTED COMPUTE</span>
              <strong>
                ~{Math.max(10, Math.round(population * 0.045))} ms / tick · ~
                {Math.max(64, Math.round(population * 0.018))} MB
              </strong>
              <small>
                {population <= 1_000
                  ? "Local tier"
                  : population <= 10_000
                    ? "Background worker recommended"
                    : "Dedicated worker required; benchmark your hardware"}
              </small>
            </aside>
            <button className="button-primary" type="submit">
              Create world
            </button>
            {error && (
              <p className="form-error" role="alert">
                {error}
              </p>
            )}
          </form>

          <div className="world-registry">
            <div className="registry-heading">
              <span>PRIVATE WORLD REGISTRY</span>
              <span>OWNER VERIFIED</span>
            </div>
            {worlds.length === 0 ? (
              <div className="registry-empty">
                <strong>No worlds yet</strong>
                <p>
                  Use the initialization console to create your first
                  deterministic world.
                </p>
              </div>
            ) : (
              worlds.map((world, index) => (
                <Link
                  className="world-row"
                  href={`/workspace/worlds/${world.id}`}
                  key={world.id}
                >
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <div>
                    <strong>{world.name}</strong>
                    <small>
                      SEED {world.settings.seed} / {world.settings.tick_rate}×
                      TICK
                    </small>
                  </div>
                  <time dateTime={world.created_at}>
                    {formatIsoDate(world.created_at)}
                  </time>
                  <b aria-hidden="true">↗</b>
                </Link>
              ))
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
