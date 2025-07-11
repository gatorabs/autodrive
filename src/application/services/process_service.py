from src.core.__init__process import *

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
            target=create_responsive_interface,
            kwargs={
                "tk_controls": tk_controls,
                "shared_frames": shared_frames,
                "shared_controls": shared_controls,
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

    if shared_controls.get("WEBVIEW"):
        processes.append(
            mp.Process(
                name="flask",
                target=start_flask_server,
                args=(shared_frames, shared_controls),
            )
        )

    return processes