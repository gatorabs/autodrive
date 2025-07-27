import multiprocessing as mp
import requests
from src.core.__init__process import (
    lane_detection_process,
    object_detection_process,
    data_sender_process,
    start_flask_server,
    shutdown_endpoint,
)
from src.infrastructure.adapters.display.ui.main_section import launch_homepage
from src.infrastructure.logging.logger import Logger

logger = Logger("ProcessManager")

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
        self.logger = logger

    def create_all_processes(self):
        self._add_lane_process()
        self._add_object_process()
        self._add_ui_process()
        if self.shared_controls.get("SEND_DATA"):
            self._add_sender_process()
        return self.processes

    def _create_process(self, name, target, **kwargs):
        process = mp.Process(
            name=name,
            target=target,
            kwargs=kwargs
        )
        self.processes.append(process)

    def _add_lane_process(self):
        self._create_process(
            name="lane",
            target=lane_detection_process,
            lane_queue=self.lane_queue,
            shared_controls=self.shared_controls,
            shared_frames=self.shared_frames,
            tk_controls=self.tk_controls,
            video_source=self.user_flags["LANE_SOURCE"]
        )

    def _add_object_process(self):
        self._create_process(
            name="object",
            target=object_detection_process,
            object_queue=self.object_queue,
            shared_controls=self.shared_controls,
            shared_frames=self.shared_frames,
            tk_controls=self.tk_controls,
            camera_source=self.user_flags["OBJECT_SOURCE"]
        )

    def _add_ui_process(self):
        self._create_process(
            name="tk",
            target=launch_homepage,
            shared_frames=self.shared_frames,
            tk_controls=self.tk_controls,
            shared_controls=self.shared_controls
        )

    def _add_sender_process(self):
        self._create_process(
            name="sender",
            target=data_sender_process,
            lane_queue=self.lane_queue,
            object_queue=self.object_queue,
            shared_controls=self.shared_controls,
            tk_controls=self.tk_controls
        )

    def handle_flask_process(self, current_webview, last_webview):
        if current_webview != last_webview:
            if current_webview:
                if self.flask_proc is None or not self.flask_proc.is_alive():
                    self.flask_proc = mp.Process(
                        name="flask",
                        target=start_flask_server,
                        args=(self.shared_frames, self.shared_controls),
                    )
                    self.flask_proc.start()
            else:
                if self.flask_proc is not None and self.flask_proc.is_alive():
                    self.logger.warning("Encerrando Server Flask via /shutdown.")

                    try:
                        requests.post(url=shutdown_endpoint, timeout=3)
                    except Exception as e:
                        self.logger.error(f"Erro ao chamar shutdown: {e}")

                    if self.flask_proc.is_alive():
                        self.logger.info("Flask Server desligado com sucesso.")
                        self.logger.info("Matando Flask Process.")
                        self.flask_proc.terminate()
                        self.flask_proc.join(timeout=3)

                    self.flask_proc = None

        return self.flask_proc, current_webview
