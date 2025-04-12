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
        "RUNNING": True,  # <- controle de execução global
        "EMERGENCY_STOP": 0,
        "SECURITY_COM": 'COM5',
        "SENDER_COM": 'COM3',
        "object_serial_data": manager.list([0, 0, 0]),
        "TARGET_BOX_HEIGHT": 200,
        "TOLERANCE": 50,
    })

    lane_queue = mp.Queue(maxsize=10)
    object_queue = mp.Queue(maxsize=10)

    lane_process = mp.Process(target=lane_detection_process, args=(lane_queue, shared_controls))
    object_process = mp.Process(target=object_detection_process, args=(object_queue, shared_controls, 0))
    sender_process = mp.Process(target=data_sender_process, args=(lane_queue, object_queue, shared_controls))
    tk_process = mp.Process(target=create_tkinter_controls, args=(shared_controls,))

    # security_proc = mp.Process(target=security_process, args=(shared_controls,))
    # trackbar_proc = mp.Process(target=object_detector_trackbar_process, args=(shared_controls,))

    processes = [lane_process, object_process, sender_process, tk_process]
    for p in processes:
        p.start()

    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        print("Interrompido pelo usuário. Encerrando processos com segurança...")
        shared_controls["RUNNING"] = False  # <- todos os processos verificam isso e saem naturalmente

        for p in processes:
            if p.is_alive():
                print(f"Forçando encerramento de: {p.name}")
                p.terminate()
