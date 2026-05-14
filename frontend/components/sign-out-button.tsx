"use client";

import { createBrowserSupabaseClient } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

export function SignOutButton() {
  const router = useRouter();
  const [signingOut, setSigningOut] = useState(false);

  async function handleSignOut() {
    setSigningOut(true);
    try {
      const supabase = createBrowserSupabaseClient();
      await supabase.auth.signOut();
      router.push("/auth/sign-in");
    } catch {
      toast.error("Sign out failed");
      setSigningOut(false);
    }
  }

  return (
    <button
      onClick={handleSignOut}
      disabled={signingOut}
      className="text-sm text-muted-foreground hover:text-foreground"
    >
      {signingOut ? "Signing out..." : "Sign out"}
    </button>
  );
}
