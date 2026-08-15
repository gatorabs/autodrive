import { ChevronLeft, ChevronRight } from "lucide-react";

interface TurnIndicatorProps {
  direction: "left" | "right";
  active: boolean;
}

export function TurnIndicator({ direction, active }: TurnIndicatorProps) {
  const Icon = direction === "left" ? ChevronLeft : ChevronRight;
  const order = direction === "left" ? [2, 1, 0] : [0, 1, 2];

  return (
    <div
      className={`flex items-center gap-0.5 border px-3 py-2.5 transition-colors ${
        active ? "border-warning/50 bg-warning-soft" : "border-border bg-surface-alt"
      }`}
      aria-label={`${direction} turn signal ${active ? "active" : "inactive"}`}
    >
      {order.map((delayIndex, i) => (
        <Icon
          key={i}
          className={`h-4 w-4 ${active ? "animate-pulse-dot text-warning" : "text-muted-foreground/40"}`}
          style={active ? { animationDelay: `${delayIndex * 150}ms` } : undefined}
        />
      ))}
    </div>
  );
}
