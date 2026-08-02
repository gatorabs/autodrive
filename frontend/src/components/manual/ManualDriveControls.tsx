import { useEffect, useState } from "react";
import { ArrowDownToLine, ChevronLeft, ChevronRight, Gauge, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { ManualControlData } from "@/types/telemetry";

interface ManualDriveControlsProps {
  onChange: (data: ManualControlData) => void;
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
      <div className="rounded-2xl border border-border bg-background/40 p-4">
        <div className="mb-3 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Gauge className="h-4 w-4 text-secondary" />
            <span className="font-semibold text-foreground">Throttle</span>
          </div>
          <button className="text-sm text-muted-foreground hover:text-foreground" onClick={() => setThrottle(0)} type="button">
            Reset
          </button>
        </div>
        <input
          type="range"
          min={0}
          max={100}
          value={throttle}
          onChange={(event) => setThrottle(Number(event.target.value))}
          className="h-2 w-full cursor-pointer appearance-none rounded-full bg-surface-soft accent-secondary"
        />
        <div className="mt-3 flex justify-between text-xs text-muted-foreground">
          <span>Stopped</span>
          <span className="font-mono text-foreground">{throttle}%</span>
          <span>Forward</span>
        </div>
      </div>

      <div className="rounded-2xl border border-border bg-background/40 p-4">
        <div className="mb-3 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <ArrowDownToLine className="h-4 w-4 text-secondary" />
            <span className="font-semibold text-foreground">Steering</span>
          </div>
          <button className="text-sm text-muted-foreground hover:text-foreground" onClick={() => setSteering(0)} type="button">
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
