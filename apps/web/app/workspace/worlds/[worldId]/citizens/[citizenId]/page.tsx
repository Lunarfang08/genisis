import Link from "next/link";
import { redirect } from "next/navigation";

import { getCitizenObservatory, getCurrentUser, getWorld } from "@/lib/api";
import { formatInteger } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function CitizenPage({
  params,
}: {
  params: Promise<{ worldId: string; citizenId: string }>;
}) {
  if (!(await getCurrentUser())) redirect("/login");
  const { worldId, citizenId } = await params;
  const world = await getWorld(worldId);
  if (!world) redirect("/workspace");
  const { profile, relationships } = await getCitizenObservatory(
    worldId,
    citizenId,
  );
  if (!profile) redirect(`/workspace/worlds/${worldId}`);

  return (
    <main className="world-detail-page citizen-page">
      <Link className="detail-back" href={`/workspace/worlds/${worldId}`}>
        ← {world.name} observatory
      </Link>
      <section className="world-detail-header">
        <div>
          <span className="eyebrow">CITIZEN / VERIFIED HISTORY</span>
          <h1>{profile.full_name}</h1>
        </div>
        <span className="stream-state">{profile.lifecycle_status}</span>
      </section>
      <section className="world-detail-grid">
        <article>
          <span>AGE / EDUCATION</span>
          <strong>
            {profile.age} / {profile.education_level}
          </strong>
        </article>
        <article>
          <span>CAREER</span>
          <strong>{profile.employment_status}</strong>
        </article>
        <article>
          <span>WEALTH</span>
          <strong>{formatInteger(profile.wealth_minor)}</strong>
        </article>
        <article>
          <span>HOUSEHOLD</span>
          <strong>{profile.household_id ?? "UNASSIGNED"}</strong>
        </article>
      </section>
      <section className="citizen-profile-grid">
        <article className="observatory-panel">
          <header>
            <span className="eyebrow">WELLBEING / PERSONALITY</span>
            <strong>REPUTATION {profile.reputation}</strong>
          </header>
          <div className="score-readout">
            {[
              ["HEALTH", profile.health],
              ["HAPPINESS", profile.happiness],
              ...Object.entries(profile.personality).map(([name, value]) => [
                name.toUpperCase(),
                value,
              ]),
            ].map(([name, value]) => (
              <div key={name}>
                <span>{name}</span>
                <strong>{value}</strong>
                <i style={{ width: `${value}%` }} />
              </div>
            ))}
          </div>
        </article>
        <article className="observatory-panel">
          <header>
            <span className="eyebrow">SOCIAL NETWORK</span>
            <strong>{relationships.length} EDGES</strong>
          </header>
          <div className="relationship-graph">
            <b>{profile.full_name}</b>
            {relationships.map((edge) => (
              <div key={`${edge.target_citizen_id}-${edge.relationship_type}`}>
                <i style={{ opacity: Math.max(0.2, edge.strength / 100) }} />
                <Link
                  href={`/workspace/worlds/${worldId}/citizens/${edge.target_citizen_id}`}
                >
                  {edge.relationship_type} /{" "}
                  {edge.target_citizen_id.slice(0, 8)}
                </Link>
                <span>TRUST {edge.trust}</span>
              </div>
            ))}
            {!relationships.length && (
              <p>No committed relationship edges for this citizen.</p>
            )}
          </div>
        </article>
        <article className="observatory-panel">
          <header>
            <span className="eyebrow">MEMORY / GOALS</span>
            <strong>{profile.memories.length} RETAINED</strong>
          </header>
          <ol className="memory-list">
            {profile.memories.map((memory) => (
              <li key={memory.id}>
                <time>{memory.occurred_on}</time>
                <strong>{memory.memory_type.replaceAll("_", " ")}</strong>
                <span>
                  IMPORTANCE {memory.importance} / RECALL {memory.recall_score}
                </span>
              </li>
            ))}
          </ol>
          <div className="goal-list">
            {profile.goals.map((goal) => (
              <div key={goal.title}>
                <span>{goal.status}</span>
                <strong>{goal.title}</strong>
                <b>{goal.priority}</b>
              </div>
            ))}
          </div>
        </article>
        <article className="observatory-panel">
          <header>
            <span className="eyebrow">MAJOR LIFE EVENTS</span>
            <strong>IMMUTABLE</strong>
          </header>
          <ol className="memory-list">
            {profile.major_events.map((event) => (
              <li key={event.id}>
                <time>{event.simulation_date}</time>
                <strong>{event.event_type.replaceAll(".", " / ")}</strong>
                <span>IMPORTANCE {event.importance}</span>
              </li>
            ))}
          </ol>
        </article>
      </section>
    </main>
  );
}
