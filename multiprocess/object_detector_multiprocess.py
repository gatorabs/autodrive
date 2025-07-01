import time
from processing.object_detection_processor import ObjectDetector
from processing.priorities_processor import set_process_priority
from extensions.logsExtension import Logger

def object_detection_process(object_queue,
                             shared_controls,
                             shared_frames,
                             tk_controls,
                             verbose=True,
                             camera_source="test_videos/people.mp4"):

    set_process_priority("high")
    object_serial_data = shared_controls["object_serial_data"]
    logger = Logger("ObjectDetection", verbose=verbose)

    object_detector = ObjectDetector(shared_serial_data=object_serial_data,
                                     shared_frames=shared_frames,
                                     tk_controls=tk_controls,
                                     camera_source=camera_source,
                                     logger=logger)

    try:
        send_interval = 0.05  # intervalo em segundos
        last_put_time = time.time()

        # Inicia loop principal de detecção
        while shared_controls.get("RUNNING", True):

            object_detector.process_frame()
            current_time = time.time()

            if (current_time - last_put_time) >= send_interval:
                object_data = {"person": object_serial_data[2], "semaforo": object_serial_data[1]}
                if not object_queue.full():
                    object_queue.put(object_data)
                last_put_time = current_time
            else:
                remaining = send_interval - (current_time - last_put_time)
                time.sleep(remaining)
    except Exception as e:
        logger.error(f"Object Detection Error:{e}")
    finally:
        object_detector.cleanup()
