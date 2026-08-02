interface StatusPillProps {
  label: string;
  tone?: "good" | "bad" | "warn" | "neutral";
}

const styles = {
  good: "border-success/25 bg-success/10 text-success",
  bad: "border-destructive/25 bg-destructive/10 text-destructive",
  warn: "border-warning/25 bg-warning/10 text-warning",
  neutral: "border-border bg-surface text-muted-foreground",
};

export function StatusPill({ label, tone = "neutral" }: StatusPillProps) {
  return (
    <span className={`inline-flex min-h-9 items-center justify-center gap-2 rounded-xl border px-3 py-1 text-xs font-medium sm:min-h-0 sm:rounded-full ${styles[tone]}`}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {label}
    </span>
  );
}
