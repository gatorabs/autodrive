interface StatusPillProps {
  label: string;
  tone?: "good" | "bad" | "warn" | "neutral";
}

const styles = {
  good: "border-emerald-400/25 bg-emerald-500/10 text-emerald-300",
  bad: "border-red-400/25 bg-red-500/10 text-red-300",
  warn: "border-amber-400/25 bg-amber-500/10 text-amber-300",
  neutral: "border-slate-700 bg-slate-900 text-slate-300",
};

export function StatusPill({ label, tone = "neutral" }: StatusPillProps) {
  return (
    <span className={`inline-flex min-h-9 items-center justify-center gap-2 rounded-xl border px-3 py-1 text-xs font-medium sm:min-h-0 sm:rounded-full ${styles[tone]}`}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {label}
    </span>
  );
}
