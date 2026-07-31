const favicon = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="10" fill="#080b0a"/>
  <path d="M32 7 57 32 32 57 7 32Z" fill="none" stroke="#b8f36b" stroke-width="3"/>
  <path d="M32 15 49 32 32 49 15 32Z" fill="none" stroke="#b8f36b" stroke-opacity=".35"/>
  <text x="32" y="39" text-anchor="middle" fill="#b8f36b" font-family="Arial,sans-serif" font-size="21" font-weight="700">G</text>
</svg>`;

export function GET() {
  return new Response(favicon, {
    headers: {
      "Cache-Control": "public, max-age=86400",
      "Content-Type": "image/svg+xml",
    },
  });
}
