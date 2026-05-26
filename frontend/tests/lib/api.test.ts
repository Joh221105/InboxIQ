import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/supabase/client", () => ({
  createBrowserSupabaseClient: () => ({
    auth: {
      getSession: async () => ({ data: { session: null } }),
    },
  }),
}));

describe("apiFetch", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("returns undefined for successful 204 responses", async () => {
    const { apiFetch } = await import("@/lib/api");
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(null, {
        status: 204,
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(apiFetch<void>("/contacts/tag-1", { method: "DELETE" })).resolves.toBeUndefined();
  });
});
