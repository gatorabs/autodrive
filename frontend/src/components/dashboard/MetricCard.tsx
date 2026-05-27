import { ReactNode } from "react";

interface MetricCardProps {
  label: string;
  value: string;
  detail?: string;
  icon?: ReactNode;
  tone?: "blue" | "green" | "orange" | "purple";
}

const tones = {
  blue: "from-blue-500/20 to-cyan-500/5 text-blue-200",
  green: "from-emerald-500/20 to-teal-500/5 text-emerald-200",
  orange: "from-orange-500/20 to-amber-500/5 text-orange-200",
  purple: "from-purple-500/20 to-fuchsia-500/5 text-purple-200",
};

export function MetricCard({ label, value, detail, icon, tone = "blue" }: MetricCardProps) {
  return (
    <div className={`rounded-2xl border border-white/10 bg-gradient-to-br ${tones[tone]} p-4`}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-slate-400">{label}</p>
          <p className="mt-2 text-2xl font-bold text-white">{value}</p>
        </div>
        {icon && <div className="rounded-xl bg-white/10 p-2 text-white">{icon}</div>}
      </div>
      {detail && <p className="mt-3 text-sm text-slate-300">{detail}</p>}
    </div>
  );
}
