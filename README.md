# Autodrive

Python application for controlling and monitoring an autonomous car, with a
CustomTkinter desktop UI, OpenCV/YOLO video processing, serial communication
with the microcontroller, and an optional Flask web panel.

Autodrive is designed as a resilient real-time control dashboard: cameras,
serial ports, control parameters, detection thresholds, perspective points, PID
values, and runtime flags can be changed while the system is running. If a
microcontroller or camera source is disconnected, the application keeps the
runtime alive and attempts to recover when the resource becomes available again.

## Demo

### Autonomous car in action

![Autonomous car driving on a marked track](docs/assets/autonomous-car-demo.gif)

### Desktop monitoring interface

![Autodrive desktop interface running with live video feeds](docs/assets/autodrive-ui.gif)

## Requirements

- Python 3.10+ recommended.
- [PyCharm](https://www.jetbrains.com/pycharm/download/) recommended, because
  it provides native support for Python interpreters, virtual environments,
  dependency installation from `requirements.txt`, run configurations, and
  debugging.
- USB camera or video file in `resources/test_videos`.
- Available serial port when microcontroller transmission is enabled.
- YOLO models downloaded/loaded locally as needed.

Open the project in PyCharm, select or create a Python interpreter, and let the
IDE install the packages listed in `requirements.txt` when prompted.

## How To Run

Open `main.py` in PyCharm and run it with the IDE run button. PyCharm will keep
the interpreter, working directory, environment, logs, and debugger in one
place, which is especially useful for this project because it starts multiple
processes and interacts with cameras and serial ports.

On startup, the application detects available cameras, lists serial ports, loads
settings from `config/`, and opens the main UI.

## Runtime Features

- Live dashboard with lane, edge, and object-detection video feeds.
- Runtime tuning for camera sources, serial ports, Canny filters, road
  perspective, PID control, operation values, and object-detection thresholds.
- Manual Mode for direct speed and steering control, including a visual steering
  wheel and dedicated manual video source.
- Task Manager view for monitoring Python process count, memory, CPU, IO, and
  per-process priority while the application is running.
- Optional Flask web panel for remote/manual speed control when `WEBVIEW` is
  enabled.

Most mutable values are stored in JSON files under `config/` and synchronized
with the shared runtime state. Slider changes are debounced before being
persisted, so the UI stays responsive while still keeping calibration values up
to date.

## Resilience

- Serial transmission is fault tolerant: if the selected microcontroller port is
  unavailable or disconnected, the sender skips failed writes and keeps trying
  to reconnect instead of crashing the application.
- Camera/video sources are monitored by their capture processes. Failed frames,
  unavailable sources, and video restarts are handled so the UI can remain open
  and recover when input becomes valid again.
- Backend processes are isolated from the UI with multiprocessing, shared
  dictionaries, and queues. This keeps expensive vision work away from the
  interface thread and allows the dashboard to continue rendering status while
  workers restart or recover.

## Performance Notes

- Camera capture, lane detection, object detection, serial sending, Flask, and
  manual mode run in separated processes when enabled.
- The desktop UI renders live frames only for the active view and pauses Task
  Manager refreshes when the view is not visible.
- Video frames are resized for the available UI area, and slider persistence is
  debounced to avoid excessive disk writes.

## Ports And Interfaces

- Desktop UI: CustomTkinter, started by the main application process.
- Web server: Flask at `http://localhost:5000`, enabled when `WEBVIEW` is turned
  on in the UI/settings.
- Shutdown Flask: `http://localhost:5000/shutdown`.
- Serial: port selected through the UI/settings, usually `SENDER_COM`.

## Cameras, Videos And Models

- Video sources are detected from the available camera indexes.
- Test videos can be placed in `resources/test_videos`.
- The base detector uses YOLO and can download/load `yolov8n.pt`.
- Custom models are discovered from training outputs such as
  `runs/detect/*/weights/best.pt`, including paths under
  `utils/model_trainer`.

## Main Flow

1. `main.py` creates shared controls with `multiprocessing.Manager`.
2. The UI prepares startup flags and calibration values.
3. `ProcessManager` starts backend processes and serial transmission.
4. Based on the flags, camera, lane detection, object detection, manual mode,
   and Flask processes are started or stopped.
5. Frames and telemetry move through shared dictionaries and queues.
6. Serial transmission publishes direction, speed, and traffic light state to
   the microcontroller.

## Organization

- `src/application`: use cases, startup flow, and process orchestration.
- `src/domain`: models, constants, and decision rules without IO dependencies.
- `src/infrastructure`: adapters, compatibility facades, persistence, logging,
  and integrations with camera, serial, Flask, OpenCV, and YOLO.
- `src/presentation`: desktop UI and visual elements.
- `utils/model_trainer`: YOLO training scripts and artifacts.
- `microcontroller`: microcontroller code.

## Architecture

This project follows a pragmatic Clean/Hexagonal architecture with a lightweight
domain:

- `domain` contains pure car decisions, such as stop, resume, speed bump,
  detour, and traffic light behavior.
- `application` coordinates processes, startup, and shared state.
- `infrastructure` integrates IO and frameworks: camera, serial, Flask, OpenCV,
  YOLO, JSON, and logging.
- `presentation` contains the desktop UI and visual rendering.

Shared state still uses `multiprocessing.Manager().dict()`, but access should
gradually go through the wrappers in `src/application/state` to reduce scattered
string keys across the codebase.

## Versioning Notes

Training directories under `utils/model_trainer/runs`, `yolo_runs`, and
`dataset` are ignored to avoid adding new large artifacts to Git. If a specific
weight file or dataset must be versioned, add it explicitly.
