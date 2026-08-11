from __future__ import annotations

# AppController: how often shared runtime state is polled and applied.
PROCESS_TICK_INTERVAL_MS = 250
FRAME_TICK_INTERVAL_MS = 33

# AppController: delay before a slider change is written to calibration_data.json.
SLIDER_PERSIST_DEBOUNCE_MS = 250

# TaskManagerView: process-list refresh interval while the tab is active.
TASK_MANAGER_POLL_INTERVAL_MS = 2000

# MainWindow: how long a transient status message stays before reverting to idle.
STATUS_MESSAGE_TIMEOUT_MS = 4000

# WarpPointsPreview: click/drag hit-test radius around a plotted corner, in pixels.
WARP_POINT_HIT_RADIUS_PX = 12.0

# MainWindow/NavRail/AppController: identifiers used to route between panels.
# Independent from any display label - a label can change without touching routing.
VIEW_HOME = "Home"
VIEW_MANUAL = "Manual"
VIEW_TASK_MANAGER = "Task Manager"
