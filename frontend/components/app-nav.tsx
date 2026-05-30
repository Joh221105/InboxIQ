"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Inbox,
  Bookmark,
  Package,
  Calendar,
  Newspaper,
  Plus,
  Settings,
  Sun,
  Moon,
} from "lucide-react";

import { SignOutButton } from "@/components/sign-out-button";
import { Bun } from "@/components/bun";
import { useTheme } from "@/components/theme-provider";
import { cn } from "@/lib/utils";

const NAV_LINKS = [
  { href: "/",          label: "Inbox",           icon: Inbox },
  { href: "/inbox",     label: "Worth Reading",    icon: Bookmark },
  { href: "/packages",  label: "Pickup Codes",     icon: Package },
  { href: "/deadlines", label: "Deadlines",        icon: Calendar },
  { href: "/digest",    label: "Digest",           icon: Newspaper },
  { href: "/settings",  label: "Settings",         icon: Settings },
];

export function AppNav() {
  const pathname = usePathname();
  const { theme, toggle } = useTheme();

  return (
    <nav
      className="flex w-[220px] shrink-0 flex-col border-r py-4"
      style={{ background: "var(--sidebar)", borderColor: "var(--sidebar-border)" }}
    >
      {/* logo */}
      <div className="mb-4 flex items-center gap-2.5 px-5 pb-1">
        <Bun size={26} envelope={false} label="InboxIQ logo" />
        <span className="font-serif text-xl font-semibold leading-none tracking-wide">
          InboxIQ
        </span>
      </div>

      {/* nav items */}
      <div className="flex flex-col gap-0.5 px-3">
        {NAV_LINKS.map((link) => {
          const active =
            link.href === "/" ? pathname === "/" : pathname.startsWith(link.href);
          const Icon = link.icon;

          return (
            <Link
              key={link.href}
              href={link.href}
              aria-current={active ? "page" : undefined}
              className={cn(
                "relative flex h-[38px] items-center gap-[11px] rounded-[calc(var(--radius)-3px)] px-3 text-sm transition-colors duration-150",
                active
                  ? "bg-accent font-semibold text-accent-foreground"
                  : "font-medium text-muted-foreground hover:bg-accent/55 hover:text-foreground",
              )}
            >
              {active && (
                <span
                  className="absolute left-0 top-2 bottom-2 w-[2.5px] rounded-full"
                  style={{ background: "var(--primary)" }}
                />
              )}
              <Icon className="size-[18px] shrink-0" strokeWidth={1.9} />
              {link.label}
            </Link>
          );
        })}
      </div>

      <div className="mt-auto px-3">
        {/* accounts section */}
        <p
          className="mb-2 px-2 text-xs font-semibold uppercase tracking-[0.06em]"
          style={{ color: "var(--muted-foreground)" }}
        >
          Accounts
        </p>
        <div className="flex flex-col gap-0.5">
          {/* placeholder connected account — real data wired via queries later */}
          <div className="flex items-center gap-2.5 rounded-lg px-2 py-1.5">
            <span
              className="size-2.5 shrink-0 rounded-full"
              style={{ background: "#C0712B" }}
            />
            <span className="truncate text-sm">Gmail connected</span>
          </div>
          <Link
            href="/settings"
            className="flex items-center gap-2.5 rounded-lg px-2 py-1.5 text-sm transition-colors duration-150 hover:bg-accent/55"
            style={{ color: "var(--muted-foreground)" }}
          >
            <Plus className="size-[15px]" />
            Connect Gmail
          </Link>
        </div>

        {/* sign out + theme toggle */}
        <div className="mt-3 border-t pt-3 flex items-center justify-between" style={{ borderColor: "var(--sidebar-border)" }}>
          <SignOutButton />
          <button
            onClick={toggle}
            aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
            className="flex size-8 items-center justify-center rounded-md transition-colors hover:bg-accent/55"
            style={{ color: "var(--muted-foreground)" }}
          >
            {theme === "dark" ? (
              <Sun className="size-[16px]" strokeWidth={1.9} />
            ) : (
              <Moon className="size-[16px]" strokeWidth={1.9} />
            )}
          </button>
        </div>
      </div>
    </nav>
  );
}
