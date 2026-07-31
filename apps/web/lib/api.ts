import type {
  AIActivity,
  Analytics,
  CitizenProfile,
  ReadinessResponse,
  ReplayStatus,
  Relationship,
  TimelineResponse,
  User,
  World,
  WorldDashboard,
  WorldMap,
} from "@/lib/shared-types";
import { headers } from "next/headers";

const defaultApiUrl = "http://127.0.0.1:8000/api/v1";

export async function getSystemReadiness(): Promise<ReadinessResponse | null> {
  const apiUrl =
    process.env.GENESIS_INTERNAL_API_URL ??
    process.env.NEXT_PUBLIC_API_URL ??
    defaultApiUrl;

  try {
    const response = await fetch(`${apiUrl}/health/ready`, {
      cache: "no-store",
      headers: { Accept: "application/json" },
      signal: AbortSignal.timeout(900),
    });

    if (!response.ok && response.status !== 503) {
      return null;
    }

    return (await response.json()) as ReadinessResponse;
  } catch {
    return null;
  }
}

export async function getCurrentUser(): Promise<User | null> {
  const requestHeaders = await headers();
  return serverApiRequest<User>("/auth/me", requestHeaders.get("cookie") ?? "");
}

export async function getWorld(worldId: string): Promise<World | null> {
  const requestHeaders = await headers();
  return serverApiRequest<World>(
    `/worlds/${encodeURIComponent(worldId)}`,
    requestHeaders.get("cookie") ?? "",
  );
}

export async function getWorlds(): Promise<World[]> {
  const requestHeaders = await headers();
  const response = await serverApiRequest<{ items: World[] }>(
    "/worlds",
    requestHeaders.get("cookie") ?? "",
  );
  return response?.items ?? [];
}

export async function getWorldObservatory(worldId: string): Promise<{
  dashboard: WorldDashboard | null;
  timeline: TimelineResponse | null;
  replay: ReplayStatus | null;
  ai: AIActivity | null;
  map: WorldMap | null;
  analytics: Analytics | null;
}> {
  const cookieHeader = (await headers()).get("cookie") ?? "";
  const encoded = encodeURIComponent(worldId);
  const [dashboard, timeline, replay, ai, map, analytics] = await Promise.all([
    serverApiRequest<WorldDashboard>(
      `/worlds/${encoded}/dashboard`,
      cookieHeader,
    ),
    serverApiRequest<TimelineResponse>(
      `/worlds/${encoded}/important-events?limit=12`,
      cookieHeader,
    ),
    serverApiRequest<ReplayStatus>(
      `/worlds/${encoded}/replay-status`,
      cookieHeader,
    ),
    serverApiRequest<AIActivity>(
      `/worlds/${encoded}/ai/activity`,
      cookieHeader,
    ),
    serverApiRequest<WorldMap>(`/worlds/${encoded}/map`, cookieHeader),
    serverApiRequest<Analytics>(`/worlds/${encoded}/analytics`, cookieHeader),
  ]);
  return { dashboard, timeline, replay, ai, map, analytics };
}

export async function getCitizenObservatory(
  worldId: string,
  citizenId: string,
): Promise<{
  profile: CitizenProfile | null;
  relationships: Relationship[];
}> {
  const cookieHeader = (await headers()).get("cookie") ?? "";
  const world = encodeURIComponent(worldId);
  const citizen = encodeURIComponent(citizenId);
  const [profile, relationships] = await Promise.all([
    serverApiRequest<CitizenProfile>(
      `/worlds/${world}/citizens/${citizen}`,
      cookieHeader,
    ),
    serverApiRequest<Relationship[]>(
      `/worlds/${world}/citizens/${citizen}/relationships`,
      cookieHeader,
    ),
  ]);
  return { profile, relationships: relationships ?? [] };
}

async function serverApiRequest<T>(
  path: string,
  cookieHeader: string,
): Promise<T | null> {
  const apiUrl =
    process.env.GENESIS_INTERNAL_API_URL ??
    process.env.NEXT_PUBLIC_API_URL ??
    defaultApiUrl;
  try {
    const response = await fetch(`${apiUrl}${path}`, {
      cache: "no-store",
      headers: { Accept: "application/json", Cookie: cookieHeader },
      signal: AbortSignal.timeout(1_500),
    });
    if (!response.ok) return null;
    return (await response.json()) as T;
  } catch {
    return null;
  }
}
