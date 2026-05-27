import { useEffect, useRef, useState } from "react";
import { endpoints } from "@/config/api";
import type { CarTelemetry } from "@/types/telemetry";

const EMPTY_TELEMETRY: Required<Pick<CarTelemetry, "car_info" | "time_info">> = {
  car_info: {
    CAR_DIRECTION_DATA: 0,
    CAR_SPEED_DATA: 0,
  },
  time_info: {
    fps: 0,
    total_processing_time: 0,
  },
};

export function useCarTelemetry(intervalMs = 500) {
  const [telemetry, setTelemetry] = useState<CarTelemetry>(EMPTY_TELEMETRY);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdatedAt, setLastUpdatedAt] = useState<Date | null>(null);
  const hadConnection = useRef(false);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const response = await fetch(endpoints.carInfo);
        if (!response.ok) {
          throw new Error(`Telemetry request failed: ${response.status}`);
        }
        const data = (await response.json()) as CarTelemetry;
        if (cancelled) return;
        setTelemetry(data);
        setIsConnected(true);
        setLastUpdatedAt(new Date());
        hadConnection.current = true;
      } catch (error) {
        if (cancelled) return;
        if (hadConnection.current) {
          console.error("Telemetry connection lost:", error);
        }
        setTelemetry(EMPTY_TELEMETRY);
        setIsConnected(false);
      }
    };

    load();
    const id = window.setInterval(load, intervalMs);

    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, [intervalMs]);

  return { telemetry, isConnected, lastUpdatedAt };
}
