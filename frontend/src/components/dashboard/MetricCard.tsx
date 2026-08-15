import { ReactNode } from "react";

interface MetricCardProps {
  label: string;
  value: string;
  detail?: string;
  icon?: ReactNode;
  tone?: "default" | "good" | "warn";
}

const tones = {
  default: "text-foreground",
  good: "text-success",
  warn: "text-warning",
};

export function MetricCard({ label, value, detail, icon, tone = "default" }: MetricCardProps) {
  return (
    <div className="flex items-center gap-3 border border-border bg-surface p-3.5 shadow-sm shadow-black/10">
      {icon && <div className="shrink-0 border border-border bg-background p-2 text-muted-foreground">{icon}</div>}
      <div className="min-w-0">
        <p className="truncate text-[0.65rem] font-semibold uppercase tracking-[0.16em] text-muted-foreground">{label}</p>
        <p className={`truncate font-mono text-lg font-bold tabular ${tones[tone]}`}>{value}</p>
        {detail && <p className="truncate text-xs text-muted-foreground">{detail}</p>}
      </div>
    </div>
  );
}
