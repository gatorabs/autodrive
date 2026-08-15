import { useEffect, useState } from "react";
import { ArrowDownToLine, ChevronLeft, ChevronRight, Gauge, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { ManualControlData } from "@/types/telemetry";

interface ManualDriveControlsProps {
  onChange: (data: ManualControlData) => void;
}

const THROTTLE_SEGMENTS = 24;

function ThrottleBar({ value }: { value: number }) {
  const litCount = Math.round((value / 100) * THROTTLE_SEGMENTS);
  return (
    <div className="flex gap-0.5">
      {Array.from({ length: THROTTLE_SEGMENTS }).map((_, i) => {
        const lit = i < litCount;
        const redline = i >= THROTTLE_SEGMENTS - 4;
        return (
          <span
            key={i}
            className={`h-7 flex-1 transition-colors ${
              lit ? (redline ? "bg-destructive" : "bg-secondary") : "bg-surface-soft"
            }`}
          />
        );
      })}
    </div>
  );
}

export function ManualDriveControls({ onChange }: ManualDriveControlsProps) {
  const [steering, setSteering] = useState(0);
  const [throttle, setThrottle] = useState(0);

  useEffect(() => {
    onChange({ x: steering, y: throttle / 100 });
  }, [onChange, steering, throttle]);

  const buttonClass = (active: boolean) =>
    active
      ? "border-secondary bg-secondary text-secondary-foreground hover:bg-secondary"
      : "border-border bg-surface text-foreground hover:bg-surface-alt";

  return (
    <div className="space-y-6">
      <div className="border border-border bg-background/40 p-4">
        <div className="mb-3 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Gauge className="h-4 w-4 text-secondary" />
            <span className="font-display text-sm font-bold uppercase tracking-wider text-foreground">Throttle</span>
          </div>
          <button className="text-xs uppercase tracking-wide text-muted-foreground hover:text-foreground" onClick={() => setThrottle(0)} type="button">
            Reset
          </button>
        </div>

        <ThrottleBar value={throttle} />
        <input
          type="range"
          min={0}
          max={100}
          value={throttle}
          onChange={(event) => setThrottle(Number(event.target.value))}
          className="mt-3 h-2 w-full cursor-pointer appearance-none rounded-none bg-surface-soft accent-secondary"
        />
        <div className="mt-3 flex justify-between font-mono text-xs text-muted-foreground">
          <span>STOPPED</span>
          <span className="text-base font-bold text-foreground">{throttle}%</span>
          <span>FULL</span>
        </div>
      </div>

      <div className="border border-border bg-background/40 p-4">
        <div className="mb-3 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <ArrowDownToLine className="h-4 w-4 text-secondary" />
            <span className="font-display text-sm font-bold uppercase tracking-wider text-foreground">Steering</span>
          </div>
          <button className="text-xs uppercase tracking-wide text-muted-foreground hover:text-foreground" onClick={() => setSteering(0)} type="button">
            Center
          </button>
        </div>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <Button className={buttonClass(steering === -1)} variant="outline" onClick={() => setSteering(-1)}>
            <ChevronLeft className="mr-2 h-5 w-5" />
            Left
          </Button>
          <Button className={buttonClass(steering === 0)} variant="outline" onClick={() => setSteering(0)}>
            <Square className="mr-2 h-4 w-4" />
            Center
          </Button>
          <Button className={buttonClass(steering === 1)} variant="outline" onClick={() => setSteering(1)}>
            Right
            <ChevronRight className="ml-2 h-5 w-5" />
          </Button>
        </div>
      </div>
    </div>
  );
}
