"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

export function WorldAutoRefresh({ running }: { running: boolean }) {
  const router = useRouter();

  useEffect(() => {
    if (!running) return;
    const timer = window.setInterval(() => router.refresh(), 2_000);
    return () => window.clearInterval(timer);
  }, [router, running]);

  return null;
}
