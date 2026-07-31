import Link from "next/link";
export default function AiTransparencyPage() {
  return (
    <main className="content-page">
      <Link className="detail-back" href="/">
        ← Overview
      </Link>
      <span className="eyebrow">AI TRANSPARENCY</span>
      <h1>Optional by design.</h1>
      <p>
        The simulation owns every fact and outcome. AI providers can turn
        selected committed events into bounded narrative annotations after
        schema validation. Caching, budgets, timeouts, circuit breakers, usage
        records, and deterministic fallbacks control cost and failure.
      </p>
      <div className="architecture-flow">
        <b>COMMITTED EVENT</b>
        <i>BOUNDED CONTEXT</i>
        <b>PROVIDER</b>
        <i>VALIDATE</i>
        <b>ANNOTATION</b>
      </div>
      <h2>Zero-cost mode</h2>
      <p>
        AI is disabled by default. The deterministic mock and the public demo
        require no key. Local Ollama is supported for demonstrations; Groq is
        opt-in.
      </p>
    </main>
  );
}
