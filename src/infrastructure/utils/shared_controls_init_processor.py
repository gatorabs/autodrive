
from src.infrastructure.constants.colors_constants import RED, RESET

def init_shared_controls(user_flags: dict, calibrated_data: dict) -> dict:
    controls = {
        **user_flags,
        "RUNNING": True,
        "object_serial_data": [0, 0, 0],
    }
    return controls


def print_initial_flags(shared_controls: dict) -> None:
    for key, value in shared_controls.items():
        if isinstance(value, bool) and not value:
            print(f"{key}: {RED}{value}{RESET}")
        else:
            print(f"{key}: {value}")