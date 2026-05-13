"use client";

import { useEffect } from "react";
import type { RefObject } from "react";

import type { Email } from "@/types";

export function shouldSkipInboxShortcut(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tagName = target.tagName.toLowerCase();
  return tagName === "input" || tagName === "textarea" || Boolean(target.isContentEditable);
}

export function getNextSelectedEmailId(
  emails: Email[],
  selectedId: string | null,
  direction: "up" | "down",
): string | null {
  if (emails.length === 0) return null;
  const index = selectedId ? emails.findIndex((email) => email.id === selectedId) : -1;
  if (index === -1) return emails[0].id;
  const nextIndex =
    direction === "down"
      ? Math.min(index + 1, emails.length - 1)
      : Math.max(index - 1, 0);
  return emails[nextIndex].id;
}

export function useEmailKeyboardNav(
  emails: Email[],
  selectedId: string | null,
  setSelectedId: (id: string | null) => void,
  onOpen: () => void,
  onArchive: () => void,
  onClose: () => void,
  searchInputRef: RefObject<HTMLInputElement>,
) {
  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (shouldSkipInboxShortcut(event.target)) return;
      if (event.key === "ArrowDown" || event.key === "j") {
        event.preventDefault();
        setSelectedId(getNextSelectedEmailId(emails, selectedId, "down"));
      } else if (event.key === "ArrowUp" || event.key === "k") {
        event.preventDefault();
        setSelectedId(getNextSelectedEmailId(emails, selectedId, "up"));
      } else if (event.key === "Enter") {
        event.preventDefault();
        onOpen();
      } else if (event.key === "e") {
        event.preventDefault();
        onArchive();
      } else if (event.key === "/") {
        event.preventDefault();
        searchInputRef.current?.focus();
      } else if (event.key === "Escape") {
        onClose();
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [emails, onArchive, onClose, onOpen, searchInputRef, selectedId, setSelectedId]);
}
