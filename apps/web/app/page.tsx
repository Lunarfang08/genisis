import Link from "next/link";

import { getSystemReadiness } from "@/lib/api";

const capabilities = [
  [
    "01",
    "Deterministic mechanics",
    "Seeded rules produce reproducible citizens, economies, governments, disease, and environmental change.",
  ],
  [
    "02",
    "Immutable history",
    "Ordered events and checksummed snapshots make every turning point inspectable and replayable.",
  ],
  [
    "03",
    "Selective AI",
    "Optional providers narrate committed facts. They never decide a simulation outcome and can remain disabled.",
  ],
  [
    "04",
    "Operational product",
    "SSE streaming, background workers, authorization, observability, containers, and quality gates support the experience.",
  ],
] as const;

export default async function Home() {
  const readiness = await getSystemReadiness();
  const online = readiness?.status === "ok";
  return (
    <div className="landing-page">
      <header className="landing-nav">
        <Link className="brand" href="/">
          <span className="brand-mark" aria-hidden="true">
            G
          </span>
          <span>
            <strong>GENESIS</strong>
            <small>civilization runtime</small>
          </span>
        </Link>
        <nav aria-label="Project navigation">
          <Link href="/architecture">Architecture</Link>
          <Link href="/technology">Technology</Link>
          <Link href="/performance">Performance</Link>
          <Link href="/ai-transparency">AI transparency</Link>
        </nav>
        <Link className="button-secondary home-action" href="/login">
          Observer login
        </Link>
      </header>

      <main>
        <section className="landing-hero">
          <div>
            <span className="eyebrow">
              ARTIFICIAL CIVILIZATION / DETERMINISTIC CORE
            </span>
            <h1>
              History you can
              <br />
              <em>prove.</em>
            </h1>
            <p>
              GENESIS simulates lives, institutions, markets, elections, and
              crises as one replayable world—not a scripted dashboard and not an
              AI guessing game.
            </p>
            <div className="landing-actions">
              <Link className="button-primary home-action" href="/demo">
                Launch interactive demo
              </Link>
              <Link className="button-secondary home-action" href="/register">
                Create a private world
              </Link>
            </div>
          </div>
          <div className="hero-runtime" aria-label="Runtime status">
            <span>RELEASE CANDIDATE / 25</span>
            <div className="hero-orbit">
              <i />
              <b>G</b>
            </div>
            <dl>
              <div>
                <dt>API</dt>
                <dd>{online ? "NOMINAL" : "LOCAL OFFLINE"}</dd>
              </div>
              <div>
                <dt>AI COST</dt>
                <dd>$0 IN DEMO MODE</dd>
              </div>
              <div>
                <dt>HISTORY</dt>
                <dd>EVENT-SOURCED</dd>
              </div>
            </dl>
          </div>
        </section>

        <section className="landing-proof" aria-label="Project capabilities">
          {capabilities.map(([index, title, body]) => (
            <article key={title}>
              <span>{index}</span>
              <h2>{title}</h2>
              <p>{body}</p>
            </article>
          ))}
        </section>

        <section className="engineering-story">
          <span className="eyebrow">WHY IT IS TECHNICALLY DIFFICULT</span>
          <h2>Thousands of agents. One coherent timeline.</h2>
          <p>
            Every batch must remain stable across machines and replays while
            transactions, live subscribers, optional narratives, and user
            controls operate around it. GENESIS separates deterministic facts
            from presentation and provider output so the world remains testable.
          </p>
          <div className="story-links">
            <Link href="/architecture">Inspect the system design →</Link>
            <Link href="/performance">Read verified scale limits →</Link>
            <a
              href="https://github.com/Lunarfang08/genisis"
              rel="noreferrer"
              target="_blank"
            >
              GitHub repository →
            </a>
          </div>
        </section>

        <section className="recruiter-summary">
          <div>
            <span className="eyebrow">ENGINEERING SIGNAL</span>
            <h2>Full-stack depth, visible.</h2>
          </div>
          <p>
            Domain modeling · deterministic systems · event sourcing · FastAPI ·
            SQLAlchemy · Next.js · real-time delivery · security · testing ·
            containers · operations
          </p>
        </section>
      </main>
      <footer>
        <span>GENESIS / RELEASE CANDIDATE</span>
        <span>Deterministic core · AI optional · Demo free</span>
        <span>2026</span>
      </footer>
    </div>
  );
}
