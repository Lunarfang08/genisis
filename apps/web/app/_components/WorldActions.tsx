"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { apiRequest } from "@/lib/browser-api";

export function WorldActions({ worldId }: { worldId: string }) {
  const router = useRouter();
  const [error, setError] = useState("");

  async function remove() {
    if (!window.confirm("Delete this world? This cannot be undone.")) return;
    try {
      await apiRequest<void>(`/worlds/${worldId}`, { method: "DELETE" });
      router.push("/workspace");
      router.refresh();
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "World deletion failed.",
      );
    }
  }

  return (
    <div className="world-actions">
      <button
        className="button-secondary danger-button"
        onClick={remove}
        type="button"
      >
        Delete world
      </button>
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
