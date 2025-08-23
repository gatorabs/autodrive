import queue
import importlib.util
from unittest.mock import MagicMock

def load_real_module():
    spec = importlib.util.spec_from_file_location(
        "real_lds", "src/infrastructure/services/lane_detection_service.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_force_safe_stop_defaults_direction():
    lds = load_real_module()
    lane_queue = queue.Queue()
    shared_controls = {}
    logger = MagicMock()

    lds.force_safe_stop(lane_queue, shared_controls, logger)

    lane_data = lane_queue.get_nowait()
    assert lane_data["CAR_DIRECTION_DATA"] == 180
    assert shared_controls["CAR_INFO"]["CAR_DIRECTION_DATA"] == 180