const defaultApiUrl = "http://127.0.0.1:8000/api/v1";
const forwardedRequestHeaders = [
  "accept",
  "content-type",
  "cookie",
  "x-csrf-token",
  "x-request-id",
] as const;
const excludedResponseHeaders = new Set([
  "connection",
  "content-encoding",
  "content-length",
  "keep-alive",
  "set-cookie",
  "transfer-encoding",
]);

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

async function proxy(
  request: Request,
  context: RouteContext,
): Promise<Response> {
  const { path } = await context.params;
  const apiUrl = (
    process.env.GENESIS_INTERNAL_API_URL ??
    process.env.NEXT_PUBLIC_API_URL ??
    defaultApiUrl
  ).replace(/\/$/, "");
  const incomingUrl = new URL(request.url);
  const targetUrl = new URL(
    `${apiUrl}/${path.map(encodeURIComponent).join("/")}${incomingUrl.search}`,
  );
  const headers = new Headers();
  for (const name of forwardedRequestHeaders) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }

  try {
    const upstream = await fetch(targetUrl, {
      method: request.method,
      headers,
      body:
        request.method === "GET" || request.method === "HEAD"
          ? undefined
          : await request.arrayBuffer(),
      cache: "no-store",
      redirect: "manual",
    });
    const responseHeaders = new Headers();
    upstream.headers.forEach((value, name) => {
      if (!excludedResponseHeaders.has(name.toLowerCase())) {
        responseHeaders.append(name, value);
      }
    });

    const cookieHeaders =
      (
        upstream.headers as Headers & {
          getSetCookie?: () => string[];
        }
      ).getSetCookie?.() ?? [];
    if (cookieHeaders.length > 0) {
      for (const cookieHeader of cookieHeaders) {
        responseHeaders.append("set-cookie", cookieHeader);
      }
    } else {
      const cookieHeader = upstream.headers.get("set-cookie");
      if (cookieHeader) responseHeaders.set("set-cookie", cookieHeader);
    }

    return new Response(upstream.body, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers: responseHeaders,
    });
  } catch {
    return Response.json(
      {
        type: "about:blank",
        title: "API unavailable",
        status: 503,
        detail: "The local GENESIS API is not reachable.",
        code: "api_unavailable",
      },
      { status: 503 },
    );
  }
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
export const OPTIONS = proxy;
