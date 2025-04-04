import time
import multiprocessing as mp

from processing.object_detection_processor import ObjectDetector
from processing.priorities_processor import set_process_priority


def object_detection_process(object_queue, shared_controls, camera_source=1):
    set_process_priority("high")
    object_serial_data = shared_controls["object_serial_data"]
    object_detector = ObjectDetector(object_serial_data, shared_controls, camera_source)
    object_detector.start()

    try:
        send_interval = 0.05  # intervalo em segundos
        last_put_time = time.time()
        while True:
            current_time = time.time()
            if (current_time - last_put_time) >= send_interval:
                object_data = {"person": object_serial_data[2], "semaforo": 0}  # 'semaforo' mockado
                if not object_queue.full():
                    object_queue.put(object_data)
                last_put_time = time.time()
            else:
                remaining = send_interval - (current_time - last_put_time)
                timer_event = mp.Event()
                timer_event.wait(remaining)
                timer_event.clear()
    except Exception as e:
        print("Object Detection Error:", e)
    finally:
        object_detector.stop()
        cv.destroyAllWindows()