from src.application.ports import SettingsStore


class SystemInitializer:
    def __init__(
        self,
        settings_store: SettingsStore,
        default_ui_path,
        camera_indices_detector,
        serial_ports_lister,
        false_color="",
        reset_color="",
    ):
        self.settings_store = settings_store
        self.default_ui_path = default_ui_path
        self.camera_indices_detector = camera_indices_detector
        self.serial_ports_lister = serial_ports_lister
        self.false_color = false_color
        self.reset_color = reset_color

    def init_shared_controls(self, user_flags):
        return {
            **user_flags,
            "RUNNING": True,
            "OBJECT_SERIAL_DATA": [0, 0, 0],
            "SAFE_STOP": False,
            "OBJ_SAFE_STOP": False,
        }

    def print_flags(self, flags: dict):
        for key, value in flags.items():
            if isinstance(value, bool) and not value:
                print(f"{key}: {self.false_color}{value}{self.reset_color}")
            else:
                print(f"{key}: {value}")

    def prepare_initial_flags(self, progress_callback=None):
        defaults_ui = self.settings_store.load(self.default_ui_path)
        if progress_callback:
            progress_callback(25)

        detected_cameras = self.camera_indices_detector()
        defaults_ui["DETECTED_CAMERAS"] = detected_cameras
        if progress_callback:
            progress_callback(50)

        available_ports = self.serial_ports_lister()
        defaults_ui["SEND_DATA"] = bool(available_ports)
        if progress_callback:
            progress_callback(75)

        defaults_ui["SENDER_COM"] = next(
            (port for port in ["COM8", "COM4"] if port in available_ports),
            available_ports[0] if available_ports else "N/A",
        )
        self.settings_store.save(defaults_ui, self.default_ui_path)
        if progress_callback:
            progress_callback(100)

        return defaults_ui
