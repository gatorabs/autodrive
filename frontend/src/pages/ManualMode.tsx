import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Gauge, Route, Timer } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AppShell } from "@/components/layout/AppShell";
import { Panel } from "@/components/common/Panel";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { VideoFeedCard } from "@/components/dashboard/VideoFeedCard";
import { ManualDriveControls } from "@/components/manual/ManualDriveControls";
import { ManualModeDialog } from "@/components/modals/ManualModeDialog";
import { endpoints } from "@/config/api";
import { useCarTelemetry } from "@/hooks/useCarTelemetry";
import type { ManualControlData } from "@/types/telemetry";

export default function ManualMode() {
  const navigate = useNavigate();
  const { telemetry, isConnected } = useCarTelemetry();
  const [controlData, setControlData] = useState<ManualControlData>({ x: 0, y: 0 });
  const [exitDialogOpen, setExitDialogOpen] = useState(false);

  const fps = Number(telemetry.time_info?.fps ?? 0);
  const frameTime = Number(telemetry.time_info?.total_processing_time ?? 0);

  useEffect(() => {
    if (!telemetry.manual_mode && telemetry.webview) {
      navigate("/");
    }
  }, [navigate, telemetry.manual_mode, telemetry.webview]);

  const handleControlChange = useCallback((data: ManualControlData) => {
    setControlData(data);
    fetch(endpoints.manualControls, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }).catch((error) => console.error("Error sending manual controls:", error));
  }, []);

  const disableManualMode = async () => {
    setExitDialogOpen(false);
    try {
      await fetch(endpoints.manualMode, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ active: false }),
      });
    } catch (error) {
      console.error("Error disabling manual mode:", error);
    }
    navigate("/");
  };

  const steeringLabel = controlData.x > 0.1 ? "Right" : controlData.x < -0.1 ? "Left" : "Center";
  const throttleLabel = controlData.y > 0.1 ? "Forward" : "Stopped";

  return (
    <AppShell
      title="Manual Mode"
      eyebrow="Direct vehicle control"
      actions={
        <Button className="w-full border border-primary bg-primary text-primary-foreground hover:bg-primary-hover sm:w-auto" onClick={() => setExitDialogOpen(true)}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Return To Dashboard
        </Button>
      }
    >
      <section className="grid gap-3 sm:grid-cols-3">
        <MetricCard label="Throttle" value={`${Math.round(controlData.y * 100)}%`} detail={throttleLabel} icon={<Gauge className="h-5 w-5" />} />
        <MetricCard label="Steering" value={steeringLabel} detail={`${Math.round(controlData.x * 45)} deg`} icon={<Route className="h-5 w-5" />} />
        <MetricCard label="Performance" value={`${fps} FPS`} detail={`${frameTime} ms frame time`} icon={<Timer className="h-5 w-5" />} tone={fps > 0 ? "good" : "warn"} />
      </section>

      <section className="mt-4 grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <VideoFeedCard title="Manual Camera" frameKey="TAB2_FRAME" connected={isConnected} />

        <Panel title="Drive Controls" subtitle="Commands are sent to /api/v2/manual-controls">
          <ManualDriveControls onChange={handleControlChange} />
        </Panel>
      </section>

      <section className="mt-4">
        <Panel title="Manual Runtime" subtitle="Current control payload">
          <div className="grid gap-3 text-sm text-muted-foreground sm:grid-cols-3">
            <Info label="Mode" value="Manual" />
            <Info label="Payload X" value={controlData.x.toFixed(2)} />
            <Info label="Payload Y" value={controlData.y.toFixed(2)} />
          </div>
        </Panel>
      </section>

      <ManualModeDialog
        open={exitDialogOpen}
        mode="disable"
        onOpenChange={setExitDialogOpen}
        onConfirm={disableManualMode}
      />
    </AppShell>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-border bg-background/50 p-4">
      <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">{label}</p>
      <p className="mt-2 text-lg font-semibold text-foreground">{value}</p>
    </div>
  );
}
