const DEFAULT_API_BASE_URL = "http://192.40.226.220:5000";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL;

export const endpoints = {
  manualMode: `${API_BASE_URL}/api/v2/manual-mode`,
  manualControls: `${API_BASE_URL}/api/v2/manual-controls`,
  carInfo: `${API_BASE_URL}/api/car-info`,
  pythonProcesses: `${API_BASE_URL}/api/v2/python-processes`,
  videoFeed: (key: string) => `${API_BASE_URL}/video_feed/${key}`,
} as const;

export type EndpointKey = keyof typeof endpoints;
