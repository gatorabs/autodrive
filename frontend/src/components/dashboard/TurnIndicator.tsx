import { ArrowLeft, ArrowRight } from "lucide-react";

interface TurnIndicatorProps {
  direction: "left" | "right";
  active: boolean;
}

export function TurnIndicator({ direction, active }: TurnIndicatorProps) {
  const Icon = direction === "left" ? ArrowLeft : ArrowRight;
  return (
    <div
      className={`flex h-11 w-11 items-center justify-center rounded-2xl border transition ${
        active
          ? "border-amber-300/40 bg-amber-400 text-slate-950 shadow-lg shadow-amber-400/20"
          : "border-white/10 bg-slate-800 text-slate-500"
      }`}
      aria-label={`${direction} turn signal ${active ? "active" : "inactive"}`}
    >
      <Icon className="h-5 w-5" />
    </div>
  );
}
