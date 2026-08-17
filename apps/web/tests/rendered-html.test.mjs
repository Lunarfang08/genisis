import assert from "node:assert/strict";
import test from "node:test";

async function render(path = "/") {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request(`http://localhost${path}`, {
      headers: { accept: "text/html" },
    }),
    {
      ASSETS: {
        fetch: async () => new Response("Not found", { status: 404 }),
      },
    },
    {
      waitUntil() {},
      passThroughOnException() {},
    },
  );
}

test("server-renders the GENESIS release landing page", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /GENESIS/);
  assert.match(html, /HISTORY YOU CAN PROVE|History you can/);
  assert.match(html, /Launch interactive demo/);
  assert.match(html, /WHY IT IS TECHNICALLY DIFFICULT/);
  assert.match(html, /AI COST/);
  assert.doesNotMatch(html, /codex-preview|Your site is taking shape/i);
});

test("renders a transparent no-login deterministic demo", async () => {
  const response = await render("/demo");
  const html = await response.text();

  assert.match(html, /NO LOGIN \/ NO PAID SERVICES/);
  assert.match(html, /Same seed \+ commands always produce the same readout/);
  assert.match(html, /transparent seeded formula/);
  assert.match(html, /makes no API or paid AI calls/);
});

test("every public detail page renders a working overview link", async () => {
  const routes = [
    "/architecture",
    "/technology",
    "/performance",
    "/ai-transparency",
    "/demo",
  ];

  for (const route of routes) {
    const response = await render(route);
    assert.equal(response.status, 200, `${route} should render`);

    const html = await response.text();
    assert.match(html, /class="detail-back"[^>]*href="\/"/);
    assert.match(html, /Overview|overview/);
  }
});
