import time

from src.core.__init__process import *
from src.infrastructure.adapters.display.ui.main_section import launch_homepage


def create_processes(shared_controls, shared_frames, tk_controls, user_flags):
    processes = []
    lane_queue = mp.Queue(maxsize=10)
    object_queue = mp.Queue(maxsize=10)

    processes.append(
        mp.Process(
            name="lane",
            target=lane_detection_process,
            kwargs={
                "lane_queue": lane_queue,
                "shared_controls": shared_controls,
                "shared_frames": shared_frames,
                "tk_controls": tk_controls,
                "video_source": user_flags["LANE_SOURCE"],
            },
        )
    )

    processes.append(
        mp.Process(
            name="object",
            target=object_detection_process,
            kwargs={
                "object_queue": object_queue,
                "shared_controls": shared_controls,
                "shared_frames": shared_frames,
                "tk_controls": tk_controls,
                "camera_source": user_flags["OBJECT_SOURCE"],
            },
        )
    )

    processes.append(
        mp.Process(
            name="tk",
            target=launch_homepage,
            kwargs={
                "shared_frames": shared_frames,
                "tk_controls": tk_controls
            },
        )
    )

    if shared_controls.get("SEND_DATA"):
        processes.append(
            mp.Process(
                name="sender",
                target=data_sender_process,
                kwargs={
                    "lane_queue": lane_queue,
                    "object_queue": object_queue,
                    "shared_controls": shared_controls,
                    "tk_controls": tk_controls
                },
            )
        )

    return processes

def handle_flask_process(current_webview,
                         last_webview,
                         flask_proc,
                         shared_frames,
                         shared_controls,
                         logger = Logger("ProcessService")):
    if current_webview != last_webview:
        if current_webview:
            if flask_proc is None or not flask_proc.is_alive():
                flask_proc = mp.Process(
                    name="flask",
                    target=start_flask_server,
                    args=(shared_frames, shared_controls)
                )
                flask_proc.start()
        else:
            if flask_proc is not None and flask_proc.is_alive():
                logger.warning("Encerrando Server Flask via /shutdown.")

                try:
                    requests.post(url=shutdown_endpoint, timeout=3)
                except Exception as e:
                    logger.error(f"Erro ao chamar shutdown: {e}")
                if flask_proc.is_alive():
                    logger.info("Flask Server desligado com sucesso.")
                    logger.info("Matando Flask Process.")
                    flask_proc.terminate()
                    flask_proc.join(timeout=3)
                flask_proc = None
    return flask_proc, current_webview

