from src.infrastructure.adapters.calibration.calibration_repository import save_data
from src.infrastructure.adapters.serial.serial_comm import SerialCommunicator
from src.infrastructure.constants.ui_constants.file_constants import DEFAULT_UI_PATH
from src.infrastructure.constants.ui_constants.flag_constants import  UI_PERSIST_FLAGS
from src.infrastructure.adapters.calibration.calibration_repository import load_data
from datetime import datetime

ts = lambda: f"[{datetime.now():%H:%M:%S}] "

def save_ui_state(tk_controls, path):
    data = {k: tk_controls.get(k) for k in UI_PERSIST_FLAGS}
    save_data(data, path)

def get_available():
    return SerialCommunicator.list_available_ports()

def get_defaults():
    defaults_ui = load_data(DEFAULT_UI_PATH)
    return (
        defaults_ui.get("SECURITY_COM", "COM1"),
        defaults_ui.get("SENDER_COM", "COM8"),
    )