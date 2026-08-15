import { ReactNode } from "react";

interface HeroReadoutProps {
  label: string;
  value: string;
  unit?: string;
  icon?: ReactNode;
  tone?: "default" | "good" | "warn" | "bad";
  accent?: "primary" | "secondary";
  sublabel?: string;
}

const toneText = {
  default: "text-foreground",
  good: "text-success",
  warn: "text-warning",
  bad: "text-destructive",
};

const accentBar = {
  primary: "bg-primary",
  secondary: "bg-secondary",
};

export function HeroReadout({ label, value, unit, icon, tone = "default", accent = "primary", sublabel }: HeroReadoutProps) {
  return (
    <div className="relative overflow-hidden border border-border bg-surface p-5 shadow-lg shadow-black/20">
      <span className={`absolute left-0 top-0 h-full w-1 ${accentBar[accent]}`} />
      <div className="flex items-center justify-between gap-3 pl-2">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">{label}</p>
        {icon && <span className="text-muted-foreground">{icon}</span>}
      </div>
      <div className="mt-1 flex items-baseline gap-2 pl-2">
        <span className={`font-display text-6xl font-bold leading-none tabular ${toneText[tone]}`}>{value}</span>
        {unit && <span className="font-mono text-sm font-medium uppercase text-muted-foreground">{unit}</span>}
      </div>
      {sublabel && <p className="mt-2 pl-2 font-mono text-xs text-muted-foreground">{sublabel}</p>}
    </div>
  );
}
