import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

sys.modules.setdefault("cv2", MagicMock())
sys.modules.setdefault("numpy", MagicMock())
sys.modules.setdefault("psutil", MagicMock())
sys.modules.setdefault("torch", MagicMock())

pil_module = types.ModuleType("PIL")
pil_image = types.ModuleType("PIL.Image")
pil_image.fromarray = MagicMock(return_value=MagicMock())
pil_module.Image = pil_image
sys.modules["PIL"] = pil_module
sys.modules["PIL.Image"] = pil_image

ultralytics_module = types.ModuleType("ultralytics")
ultralytics_module.YOLO = MagicMock()
sys.modules["ultralytics"] = ultralytics_module

serial_module = types.ModuleType("serial")
serial_tools = types.ModuleType("serial.tools")
serial_tools.list_ports = MagicMock()
serial_module.tools = serial_tools
sys.modules["serial"] = serial_module
sys.modules["serial.tools"] = serial_tools

# Stub lane detection service to avoid circular imports
lds_module = types.ModuleType("src.infrastructure.services.lane_detection_service")
lds_module.get_warp_points_from_controls = MagicMock()
lds_module.bird_eye_full = MagicMock()
lds_module.compute_distances = MagicMock(return_value=(0, 0, False, [], []))
lds_module.publish = MagicMock()
lds_module.compute_speed_and_direction = MagicMock(return_value=(0, 0))
lds_module.force_safe_stop = MagicMock()
lds_module.capture_frame_with_reopen = MagicMock(return_value=(MagicMock(), None))
lds_module.try_capture_or_mark_for_reopen = MagicMock(return_value=(MagicMock(), None))
sys.modules["src.infrastructure.services.lane_detection_service"] = lds_module
