import { ReactNode } from "react";

interface MetricCardProps {
  label: string;
  value: string;
  detail?: string;
  icon?: ReactNode;
  tone?: "default" | "good" | "warn";
}

const tones = {
  default: "border-slate-800 bg-slate-900 text-slate-300",
  good: "border-emerald-500/20 bg-slate-900 text-emerald-300",
  warn: "border-amber-500/20 bg-slate-900 text-amber-300",
};

export function MetricCard({ label, value, detail, icon, tone = "default" }: MetricCardProps) {
  return (
    <div className={`rounded-2xl border ${tones[tone]} p-4 shadow-sm shadow-black/10`}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate text-xs uppercase tracking-[0.16em] text-slate-500">{label}</p>
          <p className="mt-2 truncate text-xl font-semibold text-white sm:text-2xl">{value}</p>
        </div>
        {icon && <div className="rounded-xl border border-white/10 bg-slate-950 p-2 text-current">{icon}</div>}
      </div>
      {detail && <p className="mt-3 text-sm text-slate-300">{detail}</p>}
    </div>
  );
}
