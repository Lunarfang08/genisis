import Link from "next/link";
export default function ArchitecturePage() {
  return (
    <main className="content-page">
      <Link className="detail-back" href="/">
        ← Overview
      </Link>
      <span className="eyebrow">SYSTEM DESIGN</span>
      <h1>Architecture.</h1>
      <p>
        Browser commands travel through a same-origin proxy to an authorized
        FastAPI modular monolith. Application services coordinate PostgreSQL
        transactions with the deterministic simulation package. Immutable events
        and an outbox commit beside state; workers publish compact deltas to
        resumable SSE subscribers. Redis holds only ephemeral leases, fan-out,
        and rate limits.
      </p>
      <div className="architecture-flow">
        <b>NEXT.JS</b>
        <i>HTTP / SSE</i>
        <b>FASTAPI</b>
        <i>SERVICES</i>
        <b>SIMULATION</b>
        <i>ATOMIC COMMIT</i>
        <b>POSTGRES + OUTBOX</b>
      </div>
      <h2>Failure boundary</h2>
      <p>
        PostgreSQL is authoritative. Redis loss can degrade coordination but
        cannot erase history. AI output annotates committed events and is never
        an input to deterministic mechanics.
      </p>
    </main>
  );
}
