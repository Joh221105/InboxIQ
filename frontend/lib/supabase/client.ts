import { createBrowserClient } from "@supabase/ssr";
import type { SupabaseClient } from "@supabase/supabase-js";

const notConfigured = { error: { message: "Supabase is not configured." } };

/**
 * Browser Supabase client. Without Supabase env vars (local UI work, tests),
 * returns a stub whose auth calls report "not configured" instead of throwing.
 */
export function createBrowserSupabaseClient(): SupabaseClient {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) {
    const offlineClient = {
      auth: {
        getSession: async () => ({ data: { session: null }, error: null }),
        signOut: async () => ({ error: null }),
        signInWithPassword: async () => notConfigured,
        signUp: async () => ({ data: { session: null, user: null }, ...notConfigured }),
        resetPasswordForEmail: async () => notConfigured,
        updateUser: async () => notConfigured,
      },
    };
    return offlineClient as unknown as SupabaseClient;
  }
  return createBrowserClient(url, key);
}
