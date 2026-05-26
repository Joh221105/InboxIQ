"use client";

import { Archive, Check } from "lucide-react";
import { format } from "date-fns";

import { AccountColorDot } from "@/components/inbox/account-color-dot";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import { useEmailBody, useMarkEmailRead } from "@/lib/queries/emails";
import type { Email } from "@/types";

export function EmailDetailPanel({
  email,
  open,
  onOpenChange,
  onArchive,
}: {
  email: Email | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onArchive: (email: Email) => void;
}) {
  const bodyQuery = useEmailBody(email?.id ?? null, open);
  const markRead = useMarkEmailRead();

  return (
    <Sheet open={open && Boolean(email)} onOpenChange={onOpenChange}>
      <SheetContent onClose={() => onOpenChange(false)}>
        {email ? (
          <div className="flex min-h-full flex-col gap-5 p-6 pt-12">
            <header className="space-y-2">
              <h2 className="pr-10 text-xl font-semibold">{email.subject ?? "(no subject)"}</h2>
              <div className="text-sm text-muted-foreground">
                {email.sender_name
                  ? `${email.sender_name} <${email.sender ?? ""}>`
                  : email.sender ?? "(unknown sender)"}
                {email.received_at ? ` • ${format(new Date(email.received_at), "PPp")}` : ""}
              </div>
            </header>

            <div className="flex gap-2">
              <Button variant="outline" onClick={() => onArchive(email)}>
                <Archive className="h-4 w-4" />
                Archive
              </Button>
              <Button
                variant="outline"
                disabled={!email || email.is_read || markRead.isPending}
                onClick={() => {
                  if (email) markRead.mutate(email.id);
                }}
              >
                <Check className="h-4 w-4" />
                {email.is_read ? "Read" : "Mark Read"}
              </Button>
            </div>

            {email.action_items && email.action_items.length > 0 ? (
              <ul className="list-disc space-y-1 rounded-md border bg-muted/30 p-4 pl-8 text-sm">
                {email.action_items.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            ) : null}

            {bodyQuery.isLoading ? (
              <div className="space-y-3">
                <Skeleton className="h-5 w-3/4" />
                <Skeleton className="h-5 w-full" />
                <Skeleton className="h-64 w-full" />
              </div>
            ) : (
              <iframe
                sandbox=""
                srcDoc={bodyQuery.data?.body_html ?? ""}
                className="min-h-[400px] w-full border-0"
                title="Email body"
              />
            )}

            <footer className="mt-auto flex items-center gap-2 border-t pt-4 text-sm text-muted-foreground">
              <AccountColorDot color={email.account_color} />
              <span>{email.account_email ?? email.account_id}</span>
            </footer>
          </div>
        ) : null}
      </SheetContent>
    </Sheet>
  );
}
