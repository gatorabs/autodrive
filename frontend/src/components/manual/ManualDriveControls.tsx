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
      ? "border-blue-400 bg-blue-500 text-white hover:bg-blue-500"
      : "border-white/10 bg-slate-800 text-slate-200 hover:bg-slate-700";

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-white/10 bg-slate-950/40 p-4">
        <div className="mb-3 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Gauge className="h-4 w-4 text-blue-300" />
            <span className="font-semibold text-white">Throttle</span>
          </div>
          <button className="text-sm text-blue-300 hover:text-blue-200" onClick={() => setThrottle(0)} type="button">
            Reset
          </button>
        </div>
        <input
          type="range"
          min={0}
          max={100}
          value={throttle}
          onChange={(event) => setThrottle(Number(event.target.value))}
          className="h-2 w-full cursor-pointer appearance-none rounded-full bg-slate-700 accent-blue-400"
        />
        <div className="mt-3 flex justify-between text-xs text-slate-400">
          <span>Stopped</span>
          <span className="font-mono text-slate-200">{throttle}%</span>
          <span>Forward</span>
        </div>
      </div>

      <div className="rounded-2xl border border-white/10 bg-slate-950/40 p-4">
        <div className="mb-3 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <ArrowDownToLine className="h-4 w-4 text-blue-300" />
            <span className="font-semibold text-white">Steering</span>
          </div>
          <button className="text-sm text-blue-300 hover:text-blue-200" onClick={() => setSteering(0)} type="button">
            Center
          </button>
        </div>
        <div className="grid grid-cols-3 gap-3">
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
