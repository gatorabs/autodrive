interface StatusPillProps {
  label: string;
  tone?: "good" | "bad" | "warn" | "neutral";
  live?: boolean;
}

const styles = {
  good: "border-success/30 bg-success-soft text-success",
  bad: "border-destructive/30 bg-destructive-soft text-destructive",
  warn: "border-warning/30 bg-warning-soft text-warning",
  neutral: "border-border bg-surface text-muted-foreground",
};

export function StatusPill({ label, tone = "neutral", live = false }: StatusPillProps) {
  return (
    <span
      className={`inline-flex min-h-9 items-center justify-center gap-2 border px-3 py-1 font-mono text-[0.7rem] font-semibold uppercase tracking-[0.14em] sm:min-h-0 ${styles[tone]}`}
    >
      <span className={`h-1.5 w-1.5 rotate-45 bg-current ${live ? "animate-pulse-dot" : ""}`} />
      {label}
    </span>
  );
}
