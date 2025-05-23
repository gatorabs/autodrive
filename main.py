from core import *
import multiprocessing as mp


if __name__ == '__main__':
    mp.set_start_method('spawn')
    manager = mp.Manager()

    shared_controls = manager.dict({
        "SHOW_VIDEO": True,
        "SHOW_EDGES": True,
        "SHOW_ROI": True,
        "SHOW_PERSON_DETECTION": True,
        "SHOW_FPS": True,
        "SEND_DATA": True,
        "SECURITY_COM": 'COM5',
        "SENDER_COM": 'COM3',
        "RUNNING": True,
        "WEBVIEW": False,
        "EMERGENCY_STOP": 0,
        "object_serial_data": manager.list([0, 0, 0]),
    })

    shared_frames = manager.dict()

    lane_queue = mp.Queue(maxsize=10)
    object_queue = mp.Queue(maxsize=10)

    lane_process = mp.Process(target=lane_detection_process, args=(lane_queue, shared_controls, shared_frames))
    object_process = mp.Process(target=object_detection_process, args=(object_queue, shared_controls, shared_frames, 0))
    sender_process = mp.Process(target=data_sender_process, args=(lane_queue, object_queue, shared_controls))
    tk_process = mp.Process(target=create_tkinter_controls, args=(shared_controls,))

    processes = [lane_process, object_process, sender_process, tk_process]

    if shared_controls["WEBVIEW"]:
        flask_process = mp.Process(target=start_flask_server, args=(shared_frames, shared_controls))
        processes.append(flask_process)
        print("WEBVIEW:", shared_controls["SHOW_VIDEO"])

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