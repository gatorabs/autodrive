from src.infrastructure.constants.colors_constants import RED, RESET
from src.infrastructure.constants.ui_constants.file_constants import DEFAULT_UI_PATH
from src.infrastructure.adapters.video.begin_the_video import detect_camera_indices
from src.infrastructure.adapters.calibration.calibration_repository import load_data, save_data
from src.infrastructure.adapters.serial.serial_comm import SerialCommunicator

def init_shared_controls(user_flags):
    return {
        **user_flags,
        "RUNNING": True,
        "OBJECT_SERIAL_DATA": [0, 0, 0],
        "SAFE_STOP": False,
        "OBJ_SAFE_STOP": False
    }

def print_flags(flags: dict):
    for key, value in flags.items():
        if isinstance(value, bool) and not value:
            print(f"{key}: {RED}{value}{RESET}")
        else:
            print(f"{key}: {value}")

def prepare_initial_flags(progress_callback=None):
    defaults_ui = load_data(DEFAULT_UI_PATH)
    if progress_callback:
        progress_callback(25)

    detected_cameras = detect_camera_indices()
    defaults_ui["DETECTED_CAMERAS"] = detected_cameras
    if progress_callback:
        progress_callback(50)

    available_ports = SerialCommunicator.list_available_ports()
    defaults_ui["SEND_DATA"] = bool(available_ports)
    if progress_callback:
        progress_callback(75)

    defaults_ui["SENDER_COM"] = next(
        (port for port in ["COM8", "COM4"] if port in available_ports),
        available_ports[0] if available_ports else "N/A"
    )
    save_data(defaults_ui, DEFAULT_UI_PATH)
    if progress_callback:
        progress_callback(100)

    return defaults_ui

def terminate_if_alive(process, timeout=3):
    if process and process.is_alive():
        process.join(timeout=timeout)
        if process.is_alive():
            process.terminate()

