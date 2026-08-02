import { ReactNode } from "react";

interface MetricCardProps {
  label: string;
  value: string;
  detail?: string;
  icon?: ReactNode;
  tone?: "default" | "good" | "warn";
}

const tones = {
  default: "border-border bg-surface text-muted-foreground",
  good: "border-success/20 bg-surface text-success",
  warn: "border-warning/20 bg-surface text-warning",
};

export function MetricCard({ label, value, detail, icon, tone = "default" }: MetricCardProps) {
  return (
    <div className={`rounded-2xl border ${tones[tone]} p-4 shadow-sm shadow-black/10`}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate text-xs uppercase tracking-[0.16em] text-muted-foreground">{label}</p>
          <p className="mt-2 truncate text-xl font-semibold text-foreground sm:text-2xl">{value}</p>
        </div>
        {icon && <div className="rounded-xl border border-border bg-background p-2 text-current">{icon}</div>}
      </div>
      {detail && <p className="mt-3 text-sm text-muted-foreground">{detail}</p>}
    </div>
  );
}
