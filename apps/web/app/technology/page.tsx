import Link from "next/link";
export default function TechnologyPage() {
  return (
    <main className="content-page">
      <Link className="detail-back" href="/">
        ← Overview
      </Link>
      <span className="eyebrow">TECHNOLOGY</span>
      <h1>Built for evidence.</h1>
      <div className="landing-proof">
        <article>
          <h2>Python 3.13</h2>
          <p>
            Pure deterministic engine, FastAPI boundaries, Pydantic validation,
            SQLAlchemy 2, Alembic.
          </p>
        </article>
        <article>
          <h2>TypeScript</h2>
          <p>
            Next.js App Router, React server/client boundaries, strict
            contracts, responsive accessible UI.
          </p>
        </article>
        <article>
          <h2>Data & delivery</h2>
          <p>
            PostgreSQL event history, Redis coordination, SSE updates, non-root
            multi-stage containers.
          </p>
        </article>
        <article>
          <h2>Quality</h2>
          <p>
            Ruff, mypy, pytest, ESLint, TypeScript, rendered UI checks,
            migrations, builds, and security scans.
          </p>
        </article>
      </div>
    </main>
  );
}
