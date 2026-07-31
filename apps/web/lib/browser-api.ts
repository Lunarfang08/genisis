"use client";

import type { ProblemDetail } from "@/lib/shared-types";

const apiUrl = "/api/genesis";

function cookie(name: string): string | null {
  const prefix = `${name}=`;
  const entry = document.cookie
    .split(";")
    .map((part) => part.trim())
    .find((part) => part.startsWith(prefix));
  return entry ? decodeURIComponent(entry.slice(prefix.length)) : null;
}

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const method = (init.method ?? "GET").toUpperCase();
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body) headers.set("Content-Type", "application/json");
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    const csrf = cookie("genesis_csrf");
    if (csrf) headers.set("X-CSRF-Token", csrf);
  }

  const response = await fetch(`${apiUrl}${path}`, {
    ...init,
    headers,
    credentials: "include",
  });
  if (!response.ok) {
    const problem = (await response
      .json()
      .catch(() => null)) as ProblemDetail | null;
    throw new Error(problem?.detail ?? "The request could not be completed.");
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}
