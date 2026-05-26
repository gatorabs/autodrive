from dataclasses import dataclass
import multiprocessing as mp
from typing import Callable


def _missing_target(*args, **kwargs):
    raise RuntimeError("Process target was not configured.")


@dataclass(frozen=True)
class ProcessTargets:
    ui: Callable = _missing_target
    sender: Callable = _missing_target
    camera: Callable = _missing_target
    lane: Callable = _missing_target
    object_detection: Callable = _missing_target
    manual_video: Callable = _missing_target
    web_server: Callable = _missing_target
    web_server_shutdown: Callable = _missing_target
    lane_overlay_renderer: Callable = _missing_target
    logger_factory: Callable = _missing_target
    priority_setter: Callable = _missing_target
    video_source_manager_factory: Callable = _missing_target
    serial_communicator_factory: Callable = _missing_target
    object_detector_factory: Callable = _missing_target


class ProcessManager:
    def __init__(
        self,
        shared_controls,
        shared_frames,
        tk_controls,
        user_flags,
        *,
        targets: ProcessTargets | None = None,
        shutdown_url: str = "",
        process_factory=mp.Process,
        queue_factory=mp.Queue,
        logger=None,
    ):
        self.shared_controls = shared_controls
        self.shared_frames = shared_frames
        self.tk_controls = tk_controls
        self.user_flags = user_flags
        self.targets = targets or ProcessTargets()
        self.shutdown_url = shutdown_url
        self.process_factory = process_factory

        self.lane_queue = queue_factory(maxsize=10)
        self.object_queue = queue_factory(maxsize=10)
        self.processes = []
        self.flask_proc = None
        self.lane_proc = None
        self.object_proc = None
        self.manual_proc = None
        self.ui_proc = None
        self.sender_proc = None
        self.camera_proc = None
        self.logger = logger or self.targets.logger_factory("ProcessManager")

    def create_all_processes(self):
        self.processes.clear()
        self._add_ui_process()
        self._add_sender_process()
        return self.processes

    def _add_ui_process(self):
        self._start_process(
            "ui_proc",
            "tk",
            self.targets.ui,
            None,
            shared_frames=self.shared_frames,
            tk_controls=self.tk_controls,
            shared_controls=self.shared_controls,
            lane_queue=self.lane_queue,
        )
        if self.ui_proc:
            self.processes.append(self.ui_proc)

    def _add_sender_process(self):
        self._start_process(
            "sender_proc",
            "sender",
            self.targets.sender,
            None,
            lane_queue=self.lane_queue,
            object_queue=self.object_queue,
            shared_controls=self.shared_controls,
            tk_controls=self.tk_controls,
            logger_factory=self.targets.logger_factory,
            serial_communicator_factory=self.targets.serial_communicator_factory,
            priority_setter=self.targets.priority_setter,
        )
        if self.sender_proc:
            self.processes.append(self.sender_proc)

    def _start_process(self, attr_name, process_name, target, log_msg=None, *args, **kwargs):
        proc = getattr(self, attr_name)
        if proc is None or not proc.is_alive():
            proc = self.process_factory(name=process_name, target=target, args=args, kwargs=kwargs)
            proc.start()
            if log_msg:
                self.logger.info(log_msg)
            setattr(self, attr_name, proc)

    def _terminate_process(self, attr_name, log_msg):
        proc = getattr(self, attr_name)
        if proc and proc.is_alive():
            self.logger.warning(log_msg)
            proc.terminate()
            proc.join(timeout=3)
        setattr(self, attr_name, None)

    def start_lane_process(self):
        self._start_process(
            "lane_proc",
            "lane",
            self.targets.lane,
            "Inicializando Lane process.",
            lane_queue=self.lane_queue,
            shared_controls=self.shared_controls,
            shared_frames=self.shared_frames,
            tk_controls=self.tk_controls,
            overlay_renderer=self.targets.lane_overlay_renderer,
            logger_factory=self.targets.logger_factory,
            priority_setter=self.targets.priority_setter,
        )

    def start_camera_process(self, camera_source=None):
        source = camera_source if camera_source is not None else self.user_flags["LANE_SOURCE"]
        self._start_process(
            "camera_proc",
            "camera",
            self.targets.camera,
            "Inicializando Camera process.",
            shared_frames=self.shared_frames,
            shared_controls=self.shared_controls,
            tk_controls=self.tk_controls,
            camera_source=source,
            logger_factory=self.targets.logger_factory,
            video_source_manager_factory=self.targets.video_source_manager_factory,
            priority_setter=self.targets.priority_setter,
        )

    def start_object_process(self):
        self._start_process(
            "object_proc",
            "object",
            self.targets.object_detection,
            "Inicializando Object process.",
            object_queue=self.object_queue,
            shared_controls=self.shared_controls,
            shared_frames=self.shared_frames,
            tk_controls=self.tk_controls,
            camera_source=self.user_flags["OBJECT_SOURCE"],
            logger_factory=self.targets.logger_factory,
            video_source_manager_factory=self.targets.video_source_manager_factory,
            object_detector_factory=self.targets.object_detector_factory,
            priority_setter=self.targets.priority_setter,
        )

    def start_detection_processes(self):
        self.start_camera_process()
        self.start_lane_process()
        self.start_object_process()

    def terminate_lane_process(self):
        self._terminate_process("lane_proc", "Encerrando Lane Process.")

    def terminate_object_process(self):
        self._terminate_process("object_proc", "Encerrando Object Process.")

    def terminate_detection_processes(self):
        self.terminate_lane_process()
        self.terminate_object_process()
        self.terminate_camera_process()

    def terminate_camera_process(self):
        self._terminate_process("camera_proc", "Encerrando Camera Process.")

    def enable_manual_mode(self):
        self.terminate_lane_process()
        self.terminate_object_process()
        self.start_camera_process(camera_source=self.tk_controls.lane_source_tab2)
        self._start_process(
            "manual_proc",
            "manual_video",
            self.targets.manual_video,
            "Inicializando Manual Process.",
            shared_controls=self.shared_controls,
            shared_frames=self.shared_frames,
            lane_queue=self.lane_queue,
            logger_factory=self.targets.logger_factory,
        )

    def disable_manual_mode(self):
        self._terminate_process("manual_proc", "Encerrando Manual Process.")
        self.terminate_camera_process()
        self.start_detection_processes()

    def handle_lane_object_processes(self, current_manual_mode, last_manual_mode):
        last_manual_mode = self._handle_state_change(
            current_manual_mode, last_manual_mode, self.enable_manual_mode, self.disable_manual_mode
        )
        return (self.lane_proc, self.object_proc, self.manual_proc), last_manual_mode

    def handle_flask_process(self, current_webview, last_webview):
        def start_flask():
            self._start_process(
                "flask_proc",
                "flask",
                self.targets.web_server,
                None,
                self.shared_frames,
                self.shared_controls,
            )

        def stop_flask():
            if self.flask_proc:
                self.logger.warning("Encerrando Server Flask via /shutdown.")

                self.targets.web_server_shutdown(self.shutdown_url, self.logger)

                if self.flask_proc.is_alive():
                    self.logger.info("Flask Server 'Vivo', finalizando processo.")

                self._terminate_process("flask_proc", "Matando Flask Process.")

        last_webview = self._handle_state_change(
            current_webview, last_webview, start_flask, stop_flask
        )

        return self.flask_proc, last_webview

    @staticmethod
    def _handle_state_change(current_flag, last_flag, on_enable, on_disable):
        if current_flag != last_flag:
            if current_flag:
                on_enable()
            else:
                on_disable()
        return current_flag


__all__ = ["ProcessManager", "ProcessTargets"]
