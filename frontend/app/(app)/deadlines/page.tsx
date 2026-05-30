import { Calendar } from "lucide-react";

export default function DeadlinesPage() {
  return (
    <div className="flex min-h-full flex-col items-center justify-center gap-4 p-6">
      <div
        className="flex size-14 items-center justify-center rounded-2xl"
        style={{ background: "var(--accent)" }}
      >
        <Calendar className="size-7" style={{ color: "var(--primary)" }} strokeWidth={1.6} />
      </div>

      <h1 className="font-serif text-[28px] font-normal leading-tight text-foreground">
        Deadlines
      </h1>

      <p className="max-w-[320px] text-center text-[14.5px] leading-relaxed text-muted-foreground text-pretty">
        Bun will automatically surface deadlines and due dates from your emails.
        This feature is coming soon.
      </p>

      <span
        className="rounded-full px-3 py-1 text-xs font-medium"
        style={{ background: "var(--accent)", color: "var(--muted-foreground)" }}
      >
        Planned feature
      </span>
    </div>
  );
}
