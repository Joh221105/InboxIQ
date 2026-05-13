export function ContactTagBadge({
  tag,
}: {
  tag: { label: string; color: string } | null | undefined;
}) {
  if (!tag) return null;
  return (
    <span
      className="inline-flex shrink-0 items-center rounded-md px-2 py-0.5 text-xs font-medium text-slate-900"
      style={{ backgroundColor: tag.color }}
    >
      {tag.label}
    </span>
  );
}
