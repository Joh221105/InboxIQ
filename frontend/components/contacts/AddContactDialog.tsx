"use client";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useCreateContact } from "@/lib/queries/contacts";
import type { TagType } from "@/types";
import { useState } from "react";

const TAG_OPTIONS: { value: TagType; label: string }[] = [
  { value: "professor", label: "Professor" },
  { value: "friend", label: "Friend" },
  { value: "recruiter", label: "Recruiter" },
  { value: "custom", label: "Custom" },
];

export function AddContactDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [identifier, setIdentifier] = useState("");
  const [tag, setTag] = useState<TagType>("recruiter");
  const [customLabel, setCustomLabel] = useState("");
  const [color, setColor] = useState("#8B5CF6");
  const [error, setError] = useState<string | null>(null);

  const createContact = useCreateContact();

  function reset() {
    setIdentifier("");
    setTag("recruiter");
    setCustomLabel("");
    setColor("#8B5CF6");
    setError(null);
  }

  function handleClose(v: boolean) {
    if (!v) reset();
    onOpenChange(v);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!identifier.trim()) {
      setError("Email or domain is required");
      return;
    }
    if (tag === "custom" && !customLabel.trim()) {
      setError("Label is required for custom tags");
      return;
    }

    try {
      await createContact.mutateAsync({
        identifier: identifier.trim(),
        tag,
        custom_label: tag === "custom" ? customLabel.trim() : undefined,
        color: tag === "custom" ? color : undefined,
      });
      handleClose(false);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to add contact";
      setError(msg);
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Add Contact Tag</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 py-2">
          <div className="space-y-1">
            <Label htmlFor="identifier">Email or domain</Label>
            <Input
              id="identifier"
              placeholder="alice@example.com or @company.com"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              autoComplete="off"
            />
            <p className="text-xs text-muted-foreground">
              Use an email like <code>alice@example.com</code> or a domain like{" "}
              <code>@company.com</code> to tag all senders at that domain.
            </p>
          </div>

          <div className="space-y-1">
            <Label htmlFor="tag">Tag type</Label>
            <Select
              value={tag}
              onValueChange={(v: string | null) => {
                if (v) setTag(v as TagType);
              }}
            >
              <SelectTrigger id="tag">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {TAG_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {tag === "custom" && (
            <>
              <div className="space-y-1">
                <Label htmlFor="custom_label">Label</Label>
                <Input
                  id="custom_label"
                  placeholder="e.g. Advisor, Mentor…"
                  value={customLabel}
                  onChange={(e) => setCustomLabel(e.target.value)}
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="color">Color</Label>
                <div className="flex items-center gap-2">
                  <input
                    id="color"
                    type="color"
                    value={color}
                    onChange={(e) => setColor(e.target.value)}
                    className="h-8 w-12 cursor-pointer rounded border"
                  />
                  <span className="text-sm text-muted-foreground">{color}</span>
                </div>
              </div>
            </>
          )}

          {error && <p className="text-sm text-destructive">{error}</p>}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => handleClose(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={createContact.isPending}>
              {createContact.isPending ? "Adding…" : "Add tag"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
