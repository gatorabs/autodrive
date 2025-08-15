import multiprocessing as mp
import requests
from src.core.__init__process import (
    lane_detection_process,
    object_detection_process,
    data_sender_process,
    start_flask_server,
    shutdown_endpoint,
    manual_video_process
)
from src.infrastructure.adapters.display.ui.main_app import launch_homepage
from src.infrastructure.logging.logger import Logger

class ProcessManager:
    def __init__(self, shared_controls, shared_frames, tk_controls, user_flags):
        self.shared_controls = shared_controls
        self.shared_frames = shared_frames
        self.tk_controls = tk_controls
        self.user_flags = user_flags

        self.lane_queue = mp.Queue(maxsize=10)
        self.object_queue = mp.Queue(maxsize=10)
        self.processes = []
        self.flask_proc = None
        self.lane_proc = None
        self.object_proc = None
        self.manual_proc = None
        self.ui_proc = None
        self.sender_proc = None
        self.logger = Logger("ProcessManager")

    def create_all_processes(self):
        self.processes.clear()
        self._add_ui_process()
        self._add_sender_process()
        return self.processes

    def _add_ui_process(self):
        self._start_process(
            "ui_proc",
            "tk",
            launch_homepage,
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
            data_sender_process,
            None,
            lane_queue=self.lane_queue,
            object_queue=self.object_queue,
            shared_controls=self.shared_controls,
            tk_controls=self.tk_controls,
        )
        if self.sender_proc:
            self.processes.append(self.sender_proc)

    def _start_process(self, attr_name, process_name, target, log_msg=None, *args, **kwargs):
        proc = getattr(self, attr_name)
        if proc is None or not proc.is_alive():
            proc = mp.Process(name=process_name, target=target, args=args, kwargs=kwargs)
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
            lane_detection_process,
            "Inicializando Lane process.",
            lane_queue=self.lane_queue,
            shared_controls=self.shared_controls,
            shared_frames=self.shared_frames,
            tk_controls=self.tk_controls,
            video_source=self.user_flags["LANE_SOURCE"],
        )

    def start_object_process(self):
        self._start_process(
            "object_proc",
            "object",
            object_detection_process,
            "Inicializando Object process.",
            object_queue=self.object_queue,
            shared_controls=self.shared_controls,
            shared_frames=self.shared_frames,
            tk_controls=self.tk_controls,
            camera_source=self.user_flags["OBJECT_SOURCE"],
        )

    def start_detection_processes(self):
        self.start_lane_process()
        self.start_object_process()

    def terminate_lane_process(self):
        self._terminate_process("lane_proc", "Encerrando Lane Process.")

    def terminate_object_process(self):
        self._terminate_process("object_proc", "Encerrando Object Process.")

    def terminate_detection_processes(self):
        self.terminate_lane_process()
        self.terminate_object_process()

    def handle_lane_object_processes(self, current_manual_mode, last_manual_mode):
        def enable_manual_mode():
            self.terminate_detection_processes()
            self._start_process(
                "manual_proc",
                "manual_video",
                manual_video_process,
                "Inicializando Manual Process.",
                shared_controls=self.shared_controls,
                shared_frames=self.shared_frames,
                lane_queue=self.lane_queue,
            )

        def disable_manual_mode():
            self._terminate_process("manual_proc", "Encerrando Manual Process.")
            self.start_detection_processes()

        last_manual_mode = self._handle_state_change(
            current_manual_mode, last_manual_mode, enable_manual_mode, disable_manual_mode
        )

        return (self.lane_proc, self.object_proc, self.manual_proc), last_manual_mode

    def handle_flask_process(self, current_webview, last_webview):
        def start_flask():
            self._start_process(
                "flask_proc",
                "flask",
                start_flask_server,
                None,
                self.shared_frames,
                self.shared_controls,
            )

        def stop_flask():
            if self.flask_proc:
                self.logger.warning("Encerrando Server Flask via /shutdown.")

                try:
                    requests.post(url=shutdown_endpoint, timeout=3)
                except Exception as e:
                    self.logger.error(f"Erro ao chamar shutdown: {e}")

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
