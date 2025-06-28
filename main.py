from core import *
import multiprocessing as mp

from extensions.constants.colorsConstants import RED, RESET
from utils.flags_init import setup_flag_interface
from utils.ui import create_responsive_interface
from utils.calibration_io import load_calibration

if __name__ == '__main__':
    user_flags = setup_flag_interface()

    mp.set_start_method('spawn')
    manager = mp.Manager()

    calibrated_data = load_calibration()

    shared_controls = manager.dict({
        **user_flags,
        "RUNNING": True,
        "object_serial_data": manager.list([0, 0, 0]),
    })

    tk_controls = manager.dict(calibrated_data)

    for key, value in shared_controls.items():
        if isinstance(value, bool) and not value:
            print(f"{key}: {RED}{value}{RESET}")
        else:
            print(f"{key}: {value}")

    shared_frames = manager.dict()

    lane_source = user_flags.get("LANE_SOURCE", 0)
    object_source = user_flags.get("OBJECT_SOURCE", "test_videos/people.mp4")

    lane_queue = mp.Queue(maxsize=10)
    object_queue = mp.Queue(maxsize=10)

    lane_process = mp.Process(target=lane_detection_process,
                              args=(lane_queue, shared_controls, shared_frames, tk_controls, lane_source))
    object_process = mp.Process(target=object_detection_process,
                                args=(object_queue, shared_controls, shared_frames, tk_controls, object_source))

    sender_process = mp.Process(target=data_sender_process, args=(lane_queue, object_queue, shared_controls))
    tk_process = mp.Process(target=create_responsive_interface, args=(tk_controls, shared_frames, shared_controls))

    processes = [tk_process, lane_process, object_process, sender_process,]

    if shared_controls["WEBVIEW"]:
        flask_process = mp.Process(target=start_flask_server, args=(shared_frames, shared_controls))
        processes.append(flask_process)

    for p in processes:
        p.start()

    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        print("Interrompido pelo usuário.")
        shared_controls["RUNNING"] = False
        for p in processes:
            if p.is_alive():
                p.terminate()
