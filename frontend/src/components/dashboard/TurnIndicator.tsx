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
          ? "border-warning/40 bg-warning text-background shadow-lg shadow-warning/20"
          : "border-border bg-surface-alt text-muted-foreground"
      }`}
      aria-label={`${direction} turn signal ${active ? "active" : "inactive"}`}
    >
      <Icon className="h-5 w-5" />
    </div>
  );
}
