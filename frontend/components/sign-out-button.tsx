"use client";

import { createBrowserSupabaseClient } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";

export function SignOutButton() {
  const router = useRouter();

  async function handleSignOut() {
    const supabase = createBrowserSupabaseClient();
    await supabase.auth.signOut();
    router.push("/auth/sign-in");
  }

  return (
    <button
      onClick={handleSignOut}
      className="text-sm text-muted-foreground hover:text-foreground"
    >
      Sign out
    </button>
  );
}
