import { createBrowserClient } from "@supabase/ssr";
import type { SupabaseClient } from "@supabase/supabase-js";

export function createBrowserSupabaseClient(): SupabaseClient {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) {
    const offlineClient = {
      auth: {
        getSession: async () => ({ data: { session: null }, error: null }),
        onAuthStateChange: () => ({
          data: { subscription: { unsubscribe: () => undefined } },
        }),
        signOut: async () => ({ error: null }),
        signInWithOtp: async () => ({
          error: { message: "Supabase is not configured." },
        }),
      },
    };
    return offlineClient as unknown as SupabaseClient;
  }
  return createBrowserClient(url, key);
}
