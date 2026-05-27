export interface CarInfo {
  CAR_DIRECTION_DATA?: number;
  CAR_SPEED_DATA?: number;
}

export interface TimeInfo {
  fps?: number;
  total_processing_time?: number;
}

export interface CarTelemetry {
  car_info?: CarInfo;
  manual_mode?: boolean;
  running?: boolean;
  time_info?: TimeInfo;
  webview?: boolean;
}

export interface ManualControlData {
  x: number;
  y: number;
}

export interface ProcessInfo {
  pid: number;
  name: string;
  cpu_percent: number;
  memory_mb: number;
  io_mb: number;
  priority: string;
}

export interface SystemInfo {
  process_count: number;
  processes: ProcessInfo[];
  system_cpu: number;
  total_ram_mb: number;
}
