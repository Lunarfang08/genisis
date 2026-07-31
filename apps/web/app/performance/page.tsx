import Link from "next/link";
export default function PerformancePage() {
  return (
    <main className="content-page">
      <Link className="detail-back" href="/">
        ← Overview
      </Link>
      <span className="eyebrow">MEASURED SCALE / HONEST LIMITS</span>
      <h1>Performance.</h1>
      <p>
        GENESIS ships repeatable 1k, 10k, and 50k citizen benchmark profiles.
        Exact throughput depends on hardware, enabled systems, tick interval,
        and persistence latency; the project makes no million-citizen claim.
      </p>
      <div className="landing-proof">
        <article>
          <h2>1,000 citizens</h2>
          <p>
            Local interactive tier. In-process execution is appropriate after
            measuring your database.
          </p>
        </article>
        <article>
          <h2>10,000 citizens</h2>
          <p>
            Background worker, batches, aggregate metrics, pagination, and
            bounded graph rendering recommended.
          </p>
        </article>
        <article>
          <h2>50,000 citizens</h2>
          <p>
            Load-test tier requiring a dedicated worker and hardware-specific
            capacity review.
          </p>
        </article>
      </div>
      <p>
        Run{" "}
        <code>
          python infrastructure/scripts/benchmark_simulation.py --citizens 1000
          10000 50000
        </code>{" "}
        and record CPU, memory, engine version, and results.
      </p>
    </main>
  );
}
