import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Activity, Gauge, Radio, Route, Settings, Timer } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { AppShell } from "@/components/layout/AppShell";
import { Panel } from "@/components/common/Panel";
import { StatusPill } from "@/components/common/StatusPill";
import { HeroReadout } from "@/components/dashboard/HeroReadout";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { TurnIndicator } from "@/components/dashboard/TurnIndicator";
import { VideoFeedCard } from "@/components/dashboard/VideoFeedCard";
import { ManualModeDialog } from "@/components/modals/ManualModeDialog";
import { SystemInspectorDialog } from "@/components/modals/SystemInspectorDialog";
import { endpoints } from "@/config/api";
import { useCarTelemetry } from "@/hooks/useCarTelemetry";
import { useLogsContext } from "@/contexts/LogsContext";

const RIGHT_SIGNAL_THRESHOLD = 100;
const LEFT_SIGNAL_THRESHOLD = 80;

const feeds = [
  { title: "Normal Frame", frameKey: "NORMAL_FRAME" },
  { title: "Edges Frame", frameKey: "EDGES_FRAME" },
  { title: "Object Frame", frameKey: "OBJECT_FRAME" },
];

export default function Index() {
  const navigate = useNavigate();
  const { logs, addLog, clearLogs } = useLogsContext();
  const { telemetry, isConnected, lastUpdatedAt } = useCarTelemetry();
  const [manualDialogOpen, setManualDialogOpen] = useState(false);
  const previous = useRef({ running: false, speed: 0, direction: 0, connected: false });

  const carInfo = telemetry.car_info ?? {};
  const direction = Number(carInfo.CAR_DIRECTION_DATA ?? 0);
  const speed = Number(carInfo.CAR_SPEED_DATA ?? 0);
  const running = Boolean(telemetry.running);
  const fps = Number(telemetry.time_info?.fps ?? 0);
  const frameTime = Number(telemetry.time_info?.total_processing_time ?? 0);
  const leftSignal = direction < LEFT_SIGNAL_THRESHOLD;
  const rightSignal = direction > RIGHT_SIGNAL_THRESHOLD;

  useEffect(() => {
    if (telemetry.manual_mode && telemetry.webview) {
      navigate("/manual-mode");
    }
  }, [navigate, telemetry.manual_mode, telemetry.webview]);

  useEffect(() => {
    if (previous.current.connected !== isConnected) {
      addLog(
        isConnected ? "success" : "error",
        "system",
        isConnected ? "Dashboard connected" : "Dashboard disconnected",
        isConnected ? "Vehicle telemetry is responding." : "Unable to read vehicle telemetry.",
      );
      previous.current.connected = isConnected;
    }

    if (previous.current.running !== running) {
      addLog(running ? "success" : "warning", "system", running ? "Autonomous mode active" : "Autonomous mode inactive");
      previous.current.running = running;
      if (running) {
        toast.success("Dashboard connected to autonomous vehicle");
      }
    }

    if (previous.current.speed !== speed) {
      addLog(speed > 0 ? "success" : "warning", "motor", speed > 0 ? "DC motor running" : "DC motor stopped", `PWM: ${speed}`);
      previous.current.speed = speed;
    }

    if (previous.current.direction !== direction) {
      addLog("info", "navigation", "Steering changed", `Servo angle: ${direction} deg`);
      previous.current.direction = direction;
    }
  }, [addLog, direction, isConnected, running, speed]);

  const enableManualMode = async () => {
    setManualDialogOpen(false);
    try {
      await fetch(endpoints.manualMode, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ active: true }),
      });
    } catch (error) {
      console.error("Error enabling manual mode:", error);
    }
    navigate("/manual-mode");
  };

  return (
    <AppShell
      title="Autodrive"
      eyebrow="Live vehicle telemetry"
      actions={
        <>
          <StatusPill label={isConnected ? "Link OK" : "Link lost"} tone={isConnected ? "good" : "bad"} live={isConnected} />
          <SystemInspectorDialog logs={logs} onClearLogs={clearLogs} />
          <Button className="w-full border border-primary bg-primary text-primary-foreground hover:bg-primary-hover sm:w-auto" onClick={() => setManualDialogOpen(true)}>
            <Settings className="mr-2 h-4 w-4" />
            Manual Mode
          </Button>
        </>
      }
    >
      <section className="grid gap-3 sm:grid-cols-2">
        <HeroReadout label="Speed" value={String(speed)} unit="PWM" icon={<Gauge className="h-4 w-4" />} accent="primary" sublabel="Microcontroller command" />
        <HeroReadout
          label="Steering"
          value={String(direction)}
          unit="DEG"
          icon={<Route className="h-4 w-4" />}
          accent="secondary"
          sublabel={direction > 90 ? "Turning right" : direction < 90 ? "Turning left" : "Centered"}
        />
      </section>

      <section className="mt-3 grid gap-3 sm:grid-cols-2">
        <MetricCard label="Vehicle State" value={running ? "Active" : "Inactive"} detail={isConnected ? "Telemetry online" : "Waiting for API"} icon={<Activity className="h-4 w-4" />} tone={running ? "good" : "warn"} />
        <MetricCard label="Performance" value={`${fps} FPS`} detail={`${frameTime} ms frame time`} icon={<Timer className="h-4 w-4" />} tone={fps > 0 ? "good" : "warn"} />
      </section>

      <section className="mt-4 grid gap-4 xl:grid-cols-3">
        {feeds.map((feed) => (
          <VideoFeedCard key={feed.frameKey} {...feed} connected={isConnected} />
        ))}
      </section>

      <section className="mt-4 grid gap-4 lg:grid-cols-[1.4fr_1fr]">
        <Panel title="Turn Signals" subtitle="Direction indicators and API heartbeat">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-3">
              <TurnIndicator direction="left" active={leftSignal} />
              <TurnIndicator direction="right" active={rightSignal} />
            </div>
            <div className="grid gap-2 font-mono text-xs text-muted-foreground sm:text-right">
              <span>LAST UPDATE: {lastUpdatedAt ? lastUpdatedAt.toLocaleTimeString() : "NEVER"}</span>
              <span>WEBVIEW: {telemetry.webview ? "ENABLED" : "DISABLED"}</span>
            </div>
          </div>
        </Panel>

        <Panel title="Runtime Summary" subtitle="Current backend state">
          <div className="grid gap-3 text-sm text-muted-foreground">
            <div className="flex items-center justify-between gap-3">
              <span className="flex items-center gap-2"><Radio className="h-4 w-4 text-primary" />Manual mode</span>
              <StatusPill label={telemetry.manual_mode ? "Enabled" : "Disabled"} tone={telemetry.manual_mode ? "warn" : "neutral"} />
            </div>
            <div className="flex items-center justify-between gap-3">
              <span>Direction threshold</span>
              <span className="font-mono text-foreground">{LEFT_SIGNAL_THRESHOLD}/{RIGHT_SIGNAL_THRESHOLD}</span>
            </div>
          </div>
        </Panel>
      </section>

      <ManualModeDialog
        open={manualDialogOpen}
        mode="enable"
        onOpenChange={setManualDialogOpen}
        onConfirm={enableManualMode}
      />
    </AppShell>
  );
}
