from core import *

if __name__ == '__main__':
    mp.set_start_method('spawn')
    manager = mp.Manager()
    shared_controls = manager.dict({
       "SHOW_VIDEO": True,
       "SHOW_EDGES": True,
       "SHOW_ROI": True,
       "SHOW_PERSON_DETECTION": True,
       "SHOW_FPS": True,
       "EMERGENCY_STOP": 0,
       "SECURITY_COM": 'COM5',
       "SENDER_COM": 'COM4',
       "object_serial_data": manager.list([0, 0, 0]),
       "TARGET_BOX_HEIGHT": 200,
       "TOLERANCE": 50
    })

    lane_queue = mp.Queue(maxsize=10)
    object_queue = mp.Queue(maxsize=10)

    lane_process = mp.Process(target=lane_detection_process, args=(lane_queue, shared_controls)) # 3 PARAMETER REFERS TO CAMERA INDEX
    object_process = mp.Process(target=object_detection_process, args=(object_queue, shared_controls,0)) # 3 PARAMETER REFERS TO CAMERA INDEX
    sender_process = mp.Process(target=data_sender_process, args=(lane_queue, object_queue, shared_controls))
    security_proc = mp.Process(target=security_process, args=(shared_controls,))
    tk_process = mp.Process(target=create_tkinter_controls, args=(shared_controls,))
    #trackbar_proc = mp.Process(target=object_detector_trackbar_process, args=(shared_controls,))

    lane_process.start()
    object_process.start()
    sender_process.start()
    tk_process.start()
    security_proc.start()
    #trackbar_proc.start()

    try:
        lane_process.join()
        object_process.join()
        sender_process.join()
        tk_process.join()
        security_proc.join()
        #trackbar_proc.join()
    except KeyboardInterrupt:
        print("Interrompido pelo usuário. Encerrando processos...")
        lane_process.terminate()
        object_process.terminate()
        sender_process.terminate()
        tk_process.terminate()
        security_proc.terminate()
        #trackbar_proc.terminate()
