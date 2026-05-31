export function AccountColorDot({
  color,
  email,
  showLabel = false,
}: {
  color: string | null | undefined;
  email?: string | null;
  showLabel?: boolean;
}) {
  const domain = email?.split("@")[1];

  return (
    <div
      className="flex flex-col items-center gap-[5px]"
      title={email ?? undefined}
    >
      <span
        aria-hidden="true"
        className="h-2 w-2 shrink-0 rounded-full"
        style={{ backgroundColor: color ?? "#6b7280" }}
      />
      {showLabel && domain && (
        <span
          className="max-w-[52px] truncate text-[9px] leading-none text-muted-foreground/60"
          aria-label={`Account: ${email}`}
        >
          {domain}
        </span>
      )}
    </div>
  );
}
