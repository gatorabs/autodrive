import { useEffect, useMemo, useState } from "react";
import { Cpu, Download, FileText, HardDrive, MemoryStick, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { endpoints } from "@/config/api";
import type { LogEntry } from "@/hooks/useLogs";
import type { SystemInfo } from "@/types/telemetry";

interface SystemInspectorDialogProps {
  logs: LogEntry[];
  onClearLogs: () => void;
}

const emptySystemInfo: SystemInfo = {
  process_count: 0,
  processes: [],
  system_cpu: 0,
  total_ram_mb: 0,
};

export function SystemInspectorDialog({ logs, onClearLogs }: SystemInspectorDialogProps) {
  const [open, setOpen] = useState(false);
  const [systemInfo, setSystemInfo] = useState<SystemInfo>(emptySystemInfo);

  useEffect(() => {
    if (!open) return;

    const load = async () => {
      try {
        const response = await fetch(endpoints.pythonProcesses);
        if (!response.ok) throw new Error(`Process request failed: ${response.status}`);
        setSystemInfo(await response.json());
      } catch (error) {
        console.error("Error fetching process data:", error);
        setSystemInfo(emptySystemInfo);
      }
    };

    load();
    const id = window.setInterval(load, 8000);
    return () => window.clearInterval(id);
  }, [open]);

  const totalProcessCpu = useMemo(
    () => systemInfo.processes.reduce((total, process) => total + process.cpu_percent, 0),
    [systemInfo.processes],
  );

  const exportLogs = () => {
    const payload = logs.map((log) => ({ ...log, timestamp: log.timestamp.toISOString() }));
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `autodrive-logs-${new Date().toISOString().split("T")[0]}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  const formatMemory = (mb: number) => (mb >= 1024 ? `${(mb / 1024).toFixed(1)} GB` : `${mb.toFixed(1)} MB`);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="bg-slate-800 text-white hover:bg-slate-700">
          <FileText className="mr-2 h-4 w-4" />
          Inspector
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[86vh] w-[calc(100vw-1.5rem)] max-w-5xl overflow-hidden border-white/10 bg-slate-950 text-white">
        <DialogHeader>
          <DialogTitle>System Inspector</DialogTitle>
        </DialogHeader>

        <Tabs defaultValue="logs">
          <TabsList className="grid w-full grid-cols-2 bg-slate-900">
            <TabsTrigger value="logs">Logs</TabsTrigger>
            <TabsTrigger value="processes">Processes</TabsTrigger>
          </TabsList>

          <TabsContent value="logs" className="mt-4 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2 rounded-2xl border border-white/10 bg-slate-900 p-3">
              <Badge variant="secondary">{logs.length} events</Badge>
              <div className="flex gap-2">
                <Button size="sm" onClick={exportLogs} className="bg-blue-500 hover:bg-blue-400">
                  <Download className="mr-2 h-4 w-4" />
                  Export
                </Button>
                <Button size="sm" variant="destructive" onClick={onClearLogs}>
                  <Trash2 className="mr-2 h-4 w-4" />
                  Clear
                </Button>
              </div>
            </div>

            <ScrollArea className="h-[52vh] rounded-2xl border border-white/10 bg-slate-900 p-4">
              <div className="space-y-3">
                {logs.length === 0 ? (
                  <p className="py-12 text-center text-sm text-slate-400">No logs yet.</p>
                ) : (
                  logs.map((log) => (
                    <article key={log.id} className="rounded-2xl border border-white/10 bg-slate-950/70 p-3">
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge>{log.type}</Badge>
                        <span className="text-xs uppercase tracking-[0.16em] text-slate-400">{log.category}</span>
                        <span className="text-xs text-slate-500">{log.timestamp.toLocaleString()}</span>
                      </div>
                      <p className="mt-2 text-sm text-white">{log.message}</p>
                      {log.details && <p className="mt-1 text-xs text-slate-400">{log.details}</p>}
                    </article>
                  ))
                )}
              </div>
            </ScrollArea>
          </TabsContent>

          <TabsContent value="processes" className="mt-4 space-y-4">
            <div className="grid gap-3 sm:grid-cols-3">
              <Summary label="Python Processes" value={String(systemInfo.process_count)} />
              <Summary label="Process CPU" value={`${totalProcessCpu.toFixed(1)}%`} />
              <Summary label="Total RAM" value={formatMemory(systemInfo.total_ram_mb)} />
            </div>
            <ScrollArea className="h-[52vh] rounded-2xl border border-white/10 bg-slate-900 p-4">
              <div className="space-y-3">
                {systemInfo.processes.length === 0 ? (
                  <p className="py-12 text-center text-sm text-slate-400">No Python processes found.</p>
                ) : (
                  systemInfo.processes.map((process) => (
                    <article key={process.pid} className="rounded-2xl border border-white/10 bg-slate-950/70 p-3">
                      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                        <span className="font-mono text-sm text-blue-300">PID {process.pid}</span>
                        <Badge>{process.priority}</Badge>
                      </div>
                      <p className="mb-3 truncate text-sm text-slate-300">{process.name}</p>
                      <div className="grid gap-2 text-sm text-slate-300 sm:grid-cols-3">
                        <span className="flex items-center gap-2"><Cpu className="h-4 w-4 text-blue-300" />{process.cpu_percent.toFixed(1)}%</span>
                        <span className="flex items-center gap-2"><MemoryStick className="h-4 w-4 text-emerald-300" />{formatMemory(process.memory_mb)}</span>
                        <span className="flex items-center gap-2"><HardDrive className="h-4 w-4 text-purple-300" />{formatMemory(process.io_mb)}</span>
                      </div>
                    </article>
                  ))
                )}
              </div>
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}

function Summary({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-slate-900 p-4">
      <p className="text-xs uppercase tracking-[0.16em] text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-bold text-white">{value}</p>
    </div>
  );
}
