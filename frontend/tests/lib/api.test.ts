import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

let accessToken: string | null = null;

vi.mock("@/lib/supabase/client", () => ({
  createBrowserSupabaseClient: () => ({
    auth: {
      getSession: async () => ({
        data: { session: accessToken ? { access_token: accessToken } : null },
      }),
    },
  }),
}));

function respond(body: BodyInit | null, init: ResponseInit) {
  const fetchMock = vi.fn().mockResolvedValue(new Response(body, init));
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("apiFetch", () => {
  beforeEach(() => {
    accessToken = null;
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns undefined for successful 204 responses", async () => {
    const { apiFetch } = await import("@/lib/api");
    respond(null, { status: 204 });
    await expect(apiFetch<void>("/contacts/tag-1", { method: "DELETE" })).resolves.toBeUndefined();
  });

  it("sends the session access token as a bearer token", async () => {
    const { apiFetch } = await import("@/lib/api");
    accessToken = "token-123";
    const fetchMock = respond(JSON.stringify({ ok: true }), { status: 200 });

    await apiFetch("/users/me");

    const headers = fetchMock.mock.calls[0][1].headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer token-123");
    expect(headers.get("Content-Type")).toBe("application/json");
  });

  it("parses the backend error envelope", async () => {
    const { apiFetch } = await import("@/lib/api");
    respond(
      JSON.stringify({
        detail: { code: "duplicate_contact", message: "This sender is already tagged." },
      }),
      { status: 409, statusText: "Conflict" },
    );

    await expect(apiFetch("/contacts", { method: "POST" })).rejects.toMatchObject({
      name: "ApiError",
      status: 409,
      code: "duplicate_contact",
      message: "This sender is already tagged.",
    });
  });

  it("uses a string detail as the message", async () => {
    const { parseErrorBody } = await import("@/lib/api");
    expect(parseErrorBody({ detail: "Nope" }, "Bad Request")).toEqual({
      code: "error",
      message: "Nope",
    });
  });

  it("reports the first FastAPI validation error", async () => {
    const { parseErrorBody } = await import("@/lib/api");
    expect(
      parseErrorBody({ detail: [{ msg: "field required", loc: ["body", "tag"] }] }, "Unprocessable"),
    ).toEqual({ code: "validation_error", message: "field required" });
  });

  it("falls back to the status text for non-JSON bodies", async () => {
    const { apiFetch } = await import("@/lib/api");
    respond("<html>bad gateway</html>", { status: 502, statusText: "Bad Gateway" });
    await expect(apiFetch("/emails")).rejects.toMatchObject({
      status: 502,
      code: "unknown_error",
      message: "Bad Gateway",
    });
  });
});
