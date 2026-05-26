import Link from "next/link";

export function ContactTagBadge({
  tag,
  sender,
}: {
  tag: { label: string; color: string } | null | undefined;
  sender?: string | null;
}) {
  if (!tag) return null;
  const href = sender ? `/contacts?identifier=${encodeURIComponent(sender)}` : "/contacts";
  return (
    <Link
      href={href}
      onClick={(event) => event.stopPropagation()}
      className="inline-flex shrink-0 items-center rounded-md px-2 py-0.5 text-xs font-medium text-slate-900 transition hover:ring-1 hover:ring-slate-400"
      style={{ backgroundColor: tag.color }}
      aria-label={`Manage contact tag for ${sender ?? tag.label}`}
    >
      {tag.label}
    </Link>
  );
}
