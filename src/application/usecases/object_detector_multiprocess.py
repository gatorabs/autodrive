from src.core.__init__object import *

def object_detection_process(object_queue,
                             shared_controls,
                             shared_frames,
                             tk_controls,
                             verbose=True,
                             camera_source=None):

    set_process_priority("high")
    current_source = camera_source
    object_serial_data = shared_controls["OBJECT_SERIAL_DATA"]
    logger = Logger("ObjectDetection", verbose=verbose)

    object_detector = ObjectDetector(shared_serial_data=object_serial_data,
                                     shared_frames=shared_frames,
                                     tk_controls=tk_controls,
                                     camera_source=current_source,
                                     logger=logger)

    try:
        while shared_controls.get("RUNNING", True):
            new_cam = tk_controls.get("OBJECT_SOURCE")
            if new_cam != current_source:
                logger.info(f"Trocando Object Source de {current_source} para {new_cam}")
                object_detector.video_processor.release()

                object_detector.video_processor = VideoProcessor(
                    video_source=new_cam,
                    frame_width=FRAME_WIDTH,
                    frame_height=FRAME_HEIGHT
                )
                current_source = new_cam

            object_detector.process_frame()

            object_data = {"OBJECT_PERSON_DATA": object_serial_data[2], "TRAFFIC_LIGHT_DATA": object_serial_data[1]}
            if not object_queue.full():
                object_queue.put(object_data)

    except Exception as e:
        logger.error(f"Object Detection Error:{e}")
    finally:
        object_detector.cleanup()
