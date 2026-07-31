"use client";

import type { User } from "@/lib/shared-types";
import Link from "next/link";
import { FormEvent, useState } from "react";

import { Toast } from "@/app/_components/Toast";
import { apiRequest } from "@/lib/browser-api";

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const data = new FormData(event.currentTarget);
    const payload =
      mode === "register"
        ? {
            email: data.get("email"),
            display_name: data.get("displayName"),
            password: data.get("password"),
          }
        : { email: data.get("email"), password: data.get("password") };
    try {
      await apiRequest<{ user: User }>(`/auth/${mode}`, {
        method: "POST",
        body: JSON.stringify(payload),
      });

      // The workspace is server-protected. A full navigation guarantees the
      // freshly issued HTTP-only cookies are present on its first request.
      window.location.assign(
        mode === "register"
          ? "/workspace?auth=registered"
          : "/workspace?auth=signed-in",
      );
      return;
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Authentication failed.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-page">
      {error && (
        <Toast message={error} tone="error" onDismiss={() => setError("")} />
      )}
      <section className="auth-intro">
        <Link className="brand auth-brand" href="/">
          <span className="brand-mark" aria-hidden="true">
            G
          </span>
          <span>
            <strong>GENESIS</strong>
            <small>civilization runtime</small>
          </span>
        </Link>
        <span className="eyebrow">OBSERVER ACCESS / MILESTONE 02</span>
        <h1>
          {mode === "login"
            ? "Return to the observatory."
            : "Claim an observer identity."}
        </h1>
        <p>
          Worlds belong to their creator. Credentials are protected with
          Argon2id, rotating refresh sessions, and HTTP-only cookies.
        </p>
      </section>
      <section className="auth-card">
        <div>
          <span className="eyebrow">
            {mode === "login" ? "SIGN IN" : "CREATE ACCOUNT"}
          </span>
          <h2>{mode === "login" ? "Observer credentials" : "New observer"}</h2>
        </div>
        <form onSubmit={submit}>
          {mode === "register" && (
            <label>
              Display name
              <input
                name="displayName"
                minLength={2}
                maxLength={80}
                required
                autoComplete="name"
              />
            </label>
          )}
          <label>
            Email address
            <input name="email" type="email" required autoComplete="email" />
          </label>
          <label>
            Password
            <input
              name="password"
              type="password"
              minLength={mode === "register" ? 12 : 1}
              required
              autoComplete={
                mode === "login" ? "current-password" : "new-password"
              }
            />
          </label>
          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}
          <button
            className="button-primary auth-submit"
            disabled={busy}
            type="submit"
          >
            {busy
              ? "Authenticating…"
              : mode === "login"
                ? "Enter workspace"
                : "Create account"}
          </button>
        </form>
        <p className="auth-switch">
          {mode === "login"
            ? "No observer identity yet?"
            : "Already registered?"}{" "}
          <Link href={mode === "login" ? "/register" : "/login"}>
            {mode === "login" ? "Create one" : "Sign in"}
          </Link>
        </p>
      </section>
    </main>
  );
}
