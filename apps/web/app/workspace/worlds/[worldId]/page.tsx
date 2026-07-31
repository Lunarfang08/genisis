import Link from "next/link";
import { redirect } from "next/navigation";

import { SimulationControls } from "@/app/_components/SimulationControls";
import { HistoricalAnalytics } from "@/app/_components/HistoricalAnalytics";
import { WorldMap } from "@/app/_components/WorldMap";
import { WorldAutoRefresh } from "@/app/_components/WorldAutoRefresh";
import { WorldActions } from "@/app/_components/WorldActions";
import { getCurrentUser, getWorld, getWorldObservatory } from "@/lib/api";
import { formatInteger } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function WorldPage({
  params,
}: {
  params: Promise<{ worldId: string }>;
}) {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  const { worldId } = await params;
  const world = await getWorld(worldId);
  if (!world) redirect("/workspace");
  const { dashboard, timeline, replay, ai, map, analytics } =
    await getWorldObservatory(worldId);
  const metrics = dashboard?.latest_metrics ?? {};

  return (
    <main className="world-detail-page">
      <WorldAutoRefresh running={!world.settings.is_paused} />
      <Link className="detail-back" href="/workspace">
        ← World registry
      </Link>
      <section className="world-detail-header">
        <div>
          <span className="eyebrow">PRIVATE WORLD / OWNER VERIFIED</span>
          <h1>{world.name}</h1>
        </div>
        <span className="stream-state">OBSERVATORY ONLINE</span>
      </section>

      <SimulationControls
        initialSpeed={world.settings.tick_rate}
        worldId={world.id}
      />

      <section className="world-detail-grid" aria-label="World identity">
        <article>
          <span>DETERMINISTIC SEED</span>
          <strong>{world.settings.seed}</strong>
        </article>
        <article>
          <span>SIMULATION SPEED</span>
          <strong>{world.settings.tick_rate}×</strong>
        </article>
        <article>
          <span>CURRENT DATE / TICK</span>
          <strong>
            {world.settings.simulation_date} /{" "}
            {formatInteger(world.settings.simulation_tick)}
          </strong>
        </article>
        <article>
          <span>REPLAY TAIL</span>
          <strong>{formatInteger(replay?.replay_event_count)} EVENTS</strong>
        </article>
      </section>

      <section className="dashboard-kpis" aria-label="World vital signs">
        {[
          ["Population", dashboard?.population],
          ["GDP", metrics.gdp_minor],
          [
            "Employment",
            dashboard?.population
              ? `${Math.round(((dashboard.employed ?? 0) / dashboard.population) * 100)}%`
              : "—",
          ],
          ["Happiness", dashboard?.average_happiness],
          ["Health", dashboard?.average_health],
          ["Crime", metrics.crime_rate],
          ["Approval", metrics.government_approval],
          ["Env. risk", metrics.environmental_risk],
        ].map(([label, value]) => (
          <article key={label as string}>
            <span>{label}</span>
            <strong>
              {typeof value === "number"
                ? formatInteger(value)
                : (value ?? "—")}
            </strong>
          </article>
        ))}
      </section>

      {analytics && <HistoricalAnalytics data={analytics} />}
      {map && <WorldMap data={map} worldId={world.id} />}

      <section className="observatory-grid">
        <article className="observatory-panel economy-panel">
          <header>
            <span className="eyebrow">ECONOMY / LIVE LEDGER</span>
            <strong>{formatInteger(metrics.inflation_basis_points)} BPS</strong>
          </header>
          <div className="observatory-stats">
            <div>
              <span>GDP</span>
              <strong>{formatInteger(metrics.gdp_minor)}</strong>
            </div>
            <div>
              <span>EMPLOYED</span>
              <strong>{formatInteger(dashboard?.employed)}</strong>
            </div>
            <div>
              <span>UNEMPLOYED</span>
              <strong>{formatInteger(dashboard?.unemployed)}</strong>
            </div>
            <div>
              <span>ACTIVE FIRMS</span>
              <strong>{formatInteger(dashboard?.active_businesses)}</strong>
            </div>
            <div>
              <span>TOTAL WEALTH</span>
              <strong>{formatInteger(dashboard?.total_wealth_minor)}</strong>
            </div>
            <div>
              <span>TAX REVENUE</span>
              <strong>{formatInteger(metrics.tax_revenue)}</strong>
            </div>
          </div>
        </article>

        <article className="observatory-panel society-panel">
          <header>
            <span className="eyebrow">CITIZENS / HOUSEHOLDS</span>
            <strong>{formatInteger(dashboard?.population)} REGISTERED</strong>
          </header>
          <div className="score-readout">
            <div>
              <span>HEALTH</span>
              <strong>{formatInteger(dashboard?.average_health)}</strong>
              <i style={{ width: `${dashboard?.average_health ?? 0}%` }} />
            </div>
            <div>
              <span>HAPPINESS</span>
              <strong>{formatInteger(dashboard?.average_happiness)}</strong>
              <i style={{ width: `${dashboard?.average_happiness ?? 0}%` }} />
            </div>
            <div>
              <span>SOCIAL COHESION</span>
              <strong>{formatInteger(metrics.social_cohesion)}</strong>
              <i style={{ width: `${metrics.social_cohesion ?? 0}%` }} />
            </div>
          </div>
        </article>

        <article className="observatory-panel government-panel">
          <header>
            <span className="eyebrow">GOVERNMENT / ENVIRONMENT</span>
            <strong>DEMOCRATIC MODEL</strong>
          </header>
          <div className="observatory-stats">
            <div>
              <span>TREASURY</span>
              <strong>{formatInteger(dashboard?.treasury_minor)}</strong>
            </div>
            <div>
              <span>APPROVAL</span>
              <strong>{formatInteger(metrics.government_approval)}</strong>
            </div>
            <div>
              <span>ENV. QUALITY</span>
              <strong>{formatInteger(metrics.environmental_quality)}</strong>
            </div>
            <div>
              <span>DISEASE INDEX</span>
              <strong>{formatInteger(metrics.disease_prevalence)}</strong>
            </div>
          </div>
          <div
            className="risk-map"
            aria-label="Fictional environmental risk map"
          >
            <span>FICTIONAL RISK MAP</span>
            <i className="risk-node risk-low" />
            <i className="risk-node risk-medium" />
            <i className="risk-node risk-high" />
          </div>
        </article>

        <article className="observatory-panel ai-panel">
          <header>
            <span className="eyebrow">AI ACTIVITY / OPTIONAL</span>
            <strong>{ai?.calls ? "ENABLED" : "NO CALLS"}</strong>
          </header>
          <div className="observatory-stats">
            <div>
              <span>CALLS</span>
              <strong>{formatInteger(ai?.calls)}</strong>
            </div>
            <div>
              <span>CACHE HITS</span>
              <strong>{formatInteger(ai?.cache_hits)}</strong>
            </div>
            <div>
              <span>FAILURES</span>
              <strong>{formatInteger(ai?.failures)}</strong>
            </div>
            <div>
              <span>TOKENS</span>
              <strong>
                {formatInteger(
                  (ai?.input_tokens ?? 0) + (ai?.output_tokens ?? 0),
                )}
              </strong>
            </div>
          </div>
          <p>
            Mechanics remain deterministic. Provider output can annotate major
            committed events but never decides simulation outcomes.
          </p>
        </article>
      </section>

      <section className="timeline-panel">
        <header>
          <div>
            <span className="eyebrow">IMMUTABLE HISTORY</span>
            <h2>Major event timeline</h2>
          </div>
          <strong>
            RESUMABLE FROM #{replay?.latest_snapshot_sequence ?? 0}
          </strong>
        </header>
        {timeline?.items.length ? (
          <ol>
            {timeline.items.map((event) => (
              <li key={event.id}>
                <time>{event.simulation_date}</time>
                <div>
                  <span>{event.category}</span>
                  <strong>{event.event_type.replaceAll(".", " / ")}</strong>
                </div>
                <b>{event.importance}</b>
              </li>
            ))}
          </ol>
        ) : (
          <div className="timeline-empty">
            <strong>No major events committed yet.</strong>
            <p>
              Start or single-step the simulation. The timeline only displays
              durable history; it does not fabricate an empty world.
            </p>
          </div>
        )}
      </section>
      <nav className="export-actions" aria-label="World exports">
        <span>EXPORT VERIFIED WORLD DATA</span>
        <a href={`/api/genesis/worlds/${world.id}/export?format=json`}>JSON</a>
        <a href={`/api/genesis/worlds/${world.id}/export?format=csv`}>
          CSV event history
        </a>
        <a href={`/api/genesis/worlds/${world.id}/export?format=summary`}>
          Simulation summary
        </a>
      </nav>
      <WorldActions worldId={world.id} />
    </main>
  );
}
