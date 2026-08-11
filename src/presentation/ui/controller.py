from __future__ import annotations

from PySide6.QtCore import QObject, QThread, QTimer

from src.bootstrap import (
    build_process_manager,
    create_initializer,
    create_runtime_state,
    terminate_runtime_processes,
)
from src.infrastructure.constants.path_constants import CALIBRATION_FILE, DEFAULTS_FILE, DEFAULT_UI_PATH
from src.infrastructure.data.repository.calibration_repository import default_settings_store
from src.presentation.ui.boot import BootWindow, BootWorker

_NON_PERSISTED_KEYS = {"MANUAL_DIRECTION", "MANUAL_SPEED", "Side"}


class AppController(QObject):
    """Inherits QObject so cross-thread signal connections (e.g. BootWorker.finished)
    are correctly queued onto this object's own thread instead of running on the
    emitting thread."""

    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.settings_store = default_settings_store
        self.calibration_data: dict = {}
        self.init_data: dict = {}
        self.shared_controls = None
        self.tk_controls = None
        self.shared_frames = None
        self.user_flags: dict = {}
        self.process_manager = None
        self.processes = []
        self.last_webview = None
        self.last_manual_mode = None

        self.main_window = None
        self.boot_window: BootWindow | None = None
        self._boot_thread: QThread | None = None
        self._boot_worker: BootWorker | None = None

        self.process_timer = QTimer()
        self.process_timer.timeout.connect(self._tick_processes)
        self.frame_timer = QTimer()
        self.frame_timer.timeout.connect(self._tick_frames)

        self._persist_timers: dict[str, QTimer] = {}
        self._pending_values: dict[str, float] = {}
        self._cleaned_up = False

    def start(self) -> None:
        self.boot_window = BootWindow()
        self.boot_window.show()

        initializer, _, _ = create_initializer()
        self._boot_thread = QThread()
        self._boot_worker = BootWorker(initializer)
        self._boot_worker.moveToThread(self._boot_thread)
        self._boot_thread.started.connect(self._boot_worker.run)
        self._boot_worker.progress.connect(self.boot_window.set_progress)
        self._boot_worker.finished.connect(self._finish_boot)
        self._boot_worker.failed.connect(self.boot_window.show_error)
        self._boot_thread.start()

    def _finish_boot(self, user_flags: dict) -> None:
        self._boot_thread.quit()
        self._boot_thread.wait()

        self.boot_window.show_cuda_status(
            bool(user_flags.get("CUDA_AVAILABLE", False)),
            user_flags.get("CUDA_DEVICE_NAME", "CPU only"),
            user_flags.get("CUDA_STATUS_MESSAGE", ""),
        )
        self.shared_controls, self.tk_controls, self.shared_frames, self.user_flags = create_runtime_state(
            self.manager, user_flags
        )
        self.calibration_data = self.settings_store.load(CALIBRATION_FILE)
        self.init_data = self.settings_store.load(DEFAULT_UI_PATH)
        self.process_manager = build_process_manager(
            shared_controls=self.shared_controls,
            shared_frames=self.shared_frames,
            tk_controls=self.tk_controls,
            user_flags=user_flags,
        )
        self.processes = self.process_manager.create_backend_processes()

        from src.presentation.ui.main_window import MainWindow

        self.main_window = MainWindow(self)
        self.main_window.showMaximized()
        self.main_window.set_cuda_status(
            bool(user_flags.get("CUDA_AVAILABLE", False)), user_flags.get("CUDA_DEVICE_NAME", "CPU only")
        )
        self.boot_window.close()
        if not user_flags.get("CUDA_AVAILABLE", False):
            self.show_status(user_flags.get("CUDA_STATUS_MESSAGE", "CUDA is recommended."), "warning")

        self.process_timer.start(250)
        self.frame_timer.start(33)

    def _tick_processes(self) -> None:
        if not self.shared_controls or not self.shared_controls.is_running():
            self.close()
            return
        current_webview = self.shared_controls.webview
        current_manual_mode = self.shared_controls.manual_mode
        _, self.last_webview = self.process_manager.handle_flask_process(current_webview, self.last_webview)
        _, self.last_manual_mode = self.process_manager.handle_lane_object_processes(
            current_manual_mode, self.last_manual_mode
        )
        if not self.main_window:
            return
        if current_manual_mode:
            self.main_window.manual_view.sync_car_info()
        self.main_window.home_view.sync_dynamic_ranges()
        self.main_window.sync_state(
            current_manual_mode, self.shared_controls.safe_stop, self.shared_controls.object_safe_stop
        )

    def _tick_frames(self) -> None:
        if not self.main_window:
            return
        active = self.main_window.current_view_name
        if active == "Home" and not self.tk_controls.manual_mode:
            view = self.main_window.home_view
            view.normal_video.update_state(
                self.shared_frames.normal_frame,
                webview=self.shared_controls.webview,
                safe_stop=self.shared_controls.safe_stop,
            )
            view.edges_video.update_state(
                self.shared_frames.edges_frame,
                webview=self.shared_controls.webview,
                safe_stop=self.shared_controls.safe_stop,
            )
            view.object_video.update_state(
                self.shared_frames.object_frame,
                webview=self.shared_controls.webview,
                object_safe_stop=self.shared_controls.object_safe_stop,
            )
        elif active == "Manual" and self.tk_controls.manual_mode:
            self.main_window.manual_view.video.update_state(self.shared_frames.tab2_frame)

    def on_slider_value(self, key: str, value: float) -> None:
        self.tk_controls[key] = value
        if key in _NON_PERSISTED_KEYS:
            return
        self._pending_values[key] = value
        timer = self._persist_timers.get(key)
        if timer is None:
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(lambda k=key: self._persist_slider(k))
            self._persist_timers[key] = timer
        timer.start(250)

    def _persist_slider(self, key: str) -> None:
        if key not in self._pending_values:
            return
        value = self._pending_values.pop(key)
        self.settings_store.update({key: value}, CALIBRATION_FILE)

    def set_manual_mode(self, active: bool) -> None:
        self.tk_controls.manual_mode = active
        self.shared_controls.manual_mode = active
        self.settings_store.update({"MANUAL_MD": active}, DEFAULT_UI_PATH)

    def restore_defaults(self) -> None:
        self.settings_store.load(DEFAULTS_FILE, update_target_if_exists=self.tk_controls)
        if self.main_window:
            view = self.main_window.home_view
            for panel in (view.camera_panel, view.detection_panel, view.object_panel):
                for key, value in self.tk_controls.items():
                    panel.set_value(key, value)
        self.settings_store.update(self.tk_controls, CALIBRATION_FILE, only_existing_keys=True)
        self.show_status("Defaults restored", "success")

    def save_defaults(self) -> None:
        self.settings_store.update(self.tk_controls, DEFAULTS_FILE, only_existing_keys=True)
        self.show_status("Default saved", "success")

    def set_option(self, key: str, value: bool) -> None:
        self.tk_controls[key] = value
        self.shared_controls[key] = value

    def show_status(self, message: str, tone: str = "info") -> None:
        if self.main_window:
            self.main_window.show_status(message, tone)

    def cleanup(self) -> None:
        """Stop timers and terminate backend processes. Safe to call more than once."""
        if self._cleaned_up:
            return
        self._cleaned_up = True
        self.process_timer.stop()
        self.frame_timer.stop()
        for timer in self._persist_timers.values():
            timer.stop()
        if self.shared_controls:
            self.shared_controls.webview = False
            self.shared_controls.manual_mode = False
            self.shared_controls.request_shutdown()
        if self.process_manager:
            terminate_runtime_processes(self.processes, self.process_manager)

    def close(self) -> None:
        """Request the whole application to shut down. Safe to call from any code path."""
        self.cleanup()
        if self.main_window:
            self.main_window.close()
        elif self.boot_window:
            self.boot_window.close()
