import { createBrowserSupabaseClient } from "@/lib/supabase/client";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * Extract `{ code, message }` from a FastAPI error body. Handles the app's
 * envelope (`{detail: {code, message}}`), plain string details, and request
 * validation errors (`{detail: [{msg, ...}]}`).
 */
export function parseErrorBody(
  body: unknown,
  fallbackMessage: string,
): { code: string; message: string } {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string") {
    return { code: "error", message: detail };
  }
  if (Array.isArray(detail)) {
    const first = detail[0] as { msg?: unknown } | undefined;
    return {
      code: "validation_error",
      message: typeof first?.msg === "string" ? first.msg : fallbackMessage,
    };
  }
  if (detail && typeof detail === "object") {
    const { code, message } = detail as { code?: unknown; message?: unknown };
    return {
      code: typeof code === "string" ? code : "unknown_error",
      message: typeof message === "string" ? message : fallbackMessage,
    };
  }
  return { code: "unknown_error", message: fallbackMessage };
}

async function getAccessToken(): Promise<string | null> {
  // The backend verifies the JWT on every request, so the locally cached
  // session is sufficient here; no extra round trip to Supabase Auth.
  const { data } = await createBrowserSupabaseClient().auth.getSession();
  return data.session?.access_token ?? null;
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const token = await getAccessToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(`${API_URL}${path}`, { ...init, headers });

  if (!res.ok) {
    const body: unknown = await res.json().catch(() => null);
    const { code, message } = parseErrorBody(body, res.statusText);
    throw new ApiError(res.status, code, message);
  }

  const text = await res.text();
  return (text ? JSON.parse(text) : undefined) as T;
}
