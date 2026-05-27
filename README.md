# Autodrive

Python application for controlling and monitoring an autonomous car, with a
CustomTkinter desktop UI, OpenCV/YOLO video processing, serial communication
with the microcontroller, and an optional Flask web panel.

## Demo

### Autonomous car in action

![Autonomous car driving on a marked track](docs/assets/autonomous-car-demo.gif)

### Desktop monitoring interface

![Autodrive desktop interface running with live video feeds](docs/assets/autodrive-ui.gif)

## Requirements

- Python 3.10+ recommended.
- USB camera or video file in `resources/test_videos`.
- Available serial port when microcontroller transmission is enabled.
- YOLO models downloaded/loaded locally as needed.

Install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## How To Run

```powershell
python main.py
```

On startup, the application detects available cameras, lists serial ports, loads
settings from `config/`, and opens the main UI.

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
