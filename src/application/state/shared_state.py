from collections.abc import MutableMapping

from src.infrastructure.constants import control_keys as keys

_MISSING = object()


class SharedMapping(MutableMapping):
    """Dictionary-compatible wrapper around multiprocessing shared mappings."""

    def __init__(self, data):
        self._data = data

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        del self._data[key]

    def __iter__(self):
        return iter(self._data.keys())

    def __len__(self):
        return len(self._data)

    def get(self, key, default=None):
        return self._data.get(key, default)

    def pop(self, key, default=_MISSING):
        if default is _MISSING:
            return self._data.pop(key)
        return self._data.pop(key, default)

    def items(self):
        return self._data.items()

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def update(self, *args, **kwargs):
        return self._data.update(*args, **kwargs)

    @property
    def raw(self):
        return self._data


class RuntimeControls(SharedMapping):
    def is_running(self) -> bool:
        return bool(self.get(keys.RUNNING, True))

    def request_shutdown(self) -> None:
        self[keys.RUNNING] = False

    @property
    def webview(self) -> bool:
        return bool(self.get(keys.WEBVIEW, False))

    @webview.setter
    def webview(self, value: bool) -> None:
        self[keys.WEBVIEW] = bool(value)

    @property
    def manual_mode(self) -> bool:
        return bool(self.get(keys.MANUAL_MODE, False))

    @manual_mode.setter
    def manual_mode(self, value: bool) -> None:
        self[keys.MANUAL_MODE] = bool(value)

    @property
    def safe_stop(self) -> bool:
        return bool(self.get(keys.SAFE_STOP, False))

    @safe_stop.setter
    def safe_stop(self, value: bool) -> None:
        self[keys.SAFE_STOP] = bool(value)

    @property
    def object_safe_stop(self) -> bool:
        return bool(self.get(keys.OBJECT_SAFE_STOP, False))

    @object_safe_stop.setter
    def object_safe_stop(self, value: bool) -> None:
        self[keys.OBJECT_SAFE_STOP] = bool(value)

    @property
    def emergency_stop(self) -> int:
        return int(self.get(keys.EMERGENCY_STOP, 0) or 0)

    @emergency_stop.setter
    def emergency_stop(self, value: int) -> None:
        self[keys.EMERGENCY_STOP] = int(value)

    @property
    def car_info(self) -> dict:
        return self.get(keys.CAR_INFO, {})

    @car_info.setter
    def car_info(self, value: dict) -> None:
        self[keys.CAR_INFO] = value

    @property
    def object_serial_data(self):
        return self[keys.OBJECT_SERIAL_DATA]

    @property
    def sender_com(self):
        return self.get(keys.SENDER_COM)

    @sender_com.setter
    def sender_com(self, value) -> None:
        self[keys.SENDER_COM] = value

    @property
    def security_com(self):
        return self.get(keys.SECURITY_COM)

    @security_com.setter
    def security_com(self, value) -> None:
        self[keys.SECURITY_COM] = value

    @property
    def send_data(self) -> bool:
        return bool(self.get(keys.SEND_DATA, False))

    @send_data.setter
    def send_data(self, value: bool) -> None:
        self[keys.SEND_DATA] = bool(value)

    @property
    def speed_override(self):
        return self.get(keys.SPEED_OVERRIDE)

    def set_time_info(self, fps, avg_time) -> None:
        self[keys.TIME_INFO] = {
            "fps": round(fps, 0),
            "total_processing_time": round(avg_time, 2),
        }

    def set_max_height(self, max_height) -> None:
        self[keys.MAX_HEIGHT] = max_height


class UiControls(SharedMapping):
    @property
    def manual_mode(self) -> bool:
        return bool(self.get(keys.MANUAL_MODE, False))

    @manual_mode.setter
    def manual_mode(self, value: bool) -> None:
        self[keys.MANUAL_MODE] = bool(value)

    @property
    def lane_source(self):
        return self.get(keys.LANE_SOURCE)

    @lane_source.setter
    def lane_source(self, value) -> None:
        self[keys.LANE_SOURCE] = value

    @property
    def lane_source_tab2(self):
        return self.get(keys.LANE_SOURCE_TAB2)

    @lane_source_tab2.setter
    def lane_source_tab2(self, value) -> None:
        self[keys.LANE_SOURCE_TAB2] = value

    @property
    def object_source(self):
        return self.get(keys.OBJECT_SOURCE)

    @object_source.setter
    def object_source(self, value) -> None:
        self[keys.OBJECT_SOURCE] = value

    @property
    def send_logs(self) -> bool:
        return bool(self.get(keys.SEND_LOGS, False))

    @property
    def show_info(self) -> bool:
        return bool(self.get(keys.SHOW_INFO, False))

    @property
    def show_lines(self) -> bool:
        return bool(self.get(keys.SHOW_LINES, False))

    @property
    def show_roi(self) -> bool:
        return bool(self.get(keys.SHOW_ROI, False))

    @property
    def speed(self):
        return self.get(keys.SPEED)

    @speed.setter
    def speed(self, value) -> None:
        self[keys.SPEED] = value

    @property
    def side(self):
        return self.get(keys.SIDE, 1)

    @side.setter
    def side(self, value) -> None:
        self[keys.SIDE] = value

    @property
    def distance(self):
        return self.get(keys.DISTANCE)


class SharedFrames(SharedMapping):
    @property
    def camera_frame(self):
        return self.get(keys.CAMERA_FRAME)

    @camera_frame.setter
    def camera_frame(self, frame) -> None:
        self[keys.CAMERA_FRAME] = frame

    @property
    def normal_frame(self):
        return self.get(keys.NORMAL_FRAME)

    @normal_frame.setter
    def normal_frame(self, frame) -> None:
        self[keys.NORMAL_FRAME] = frame

    @property
    def edges_frame(self):
        return self.get(keys.EDGES_FRAME)

    @edges_frame.setter
    def edges_frame(self, frame) -> None:
        self[keys.EDGES_FRAME] = frame

    @property
    def object_frame(self):
        return self.get(keys.OBJECT_FRAME)

    @object_frame.setter
    def object_frame(self, frame) -> None:
        self[keys.OBJECT_FRAME] = frame

    @property
    def tab2_frame(self):
        return self.get(keys.TAB2_FRAME)

    @tab2_frame.setter
    def tab2_frame(self, frame) -> None:
        self[keys.TAB2_FRAME] = frame

    def publish_lane_frames(self, normal_frame, edges_frame) -> None:
        self.normal_frame = normal_frame
        self.edges_frame = edges_frame
