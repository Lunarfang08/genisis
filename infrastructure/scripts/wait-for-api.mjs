const endpoint =
  process.env.GENESIS_WAIT_URL ??
  "http://localhost:8000/api/v1/health/ready";
const timeoutMs = Number(process.env.GENESIS_WAIT_TIMEOUT_MS ?? 60_000);
const deadline = Date.now() + timeoutMs;

while (Date.now() < deadline) {
  try {
    const response = await fetch(endpoint);
    if (response.ok) {
      console.log(`Ready: ${endpoint}`);
      process.exit(0);
    }
  } catch {
    // The service is still starting.
  }

  await new Promise((resolve) => setTimeout(resolve, 1_000));
}

console.error(`Timed out waiting for ${endpoint}`);
process.exit(1);

