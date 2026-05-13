export function AccountColorDot({ color }: { color: string | null | undefined }) {
  return (
    <span
      aria-hidden="true"
      className="h-2 w-2 shrink-0 rounded-full"
      style={{ backgroundColor: color ?? "#6b7280" }}
    />
  );
}
