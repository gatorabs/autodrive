from src.infrastructure.constants.ui_constants.file_constants import DEFAULT_UI_PATH
from src.infrastructure.adapters.video.begin_the_video import detect_camera_indices
from src.infrastructure.adapters.calibration.calibration_repository import load_data, save_data
from src.infrastructure.adapters.serial.serial_comm import SerialCommunicator
from src.infrastructure.logging.logger import Logger

logger = Logger("CalibrationUI", verbose=True)

def prepare_initial_flags():
    defaults_ui = load_data(DEFAULT_UI_PATH)
    detected_cameras = detect_camera_indices()
    defaults_ui["DETECTED_CAMERAS"] = detected_cameras

    available_ports = SerialCommunicator.list_available_ports()
    if available_ports is not None:
        defaults_ui["SEND_DATA"] = True
    save_data(defaults_ui, DEFAULT_UI_PATH)
    return defaults_ui
