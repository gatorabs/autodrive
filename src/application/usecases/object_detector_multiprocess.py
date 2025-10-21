from src.infrastructure.adapters.detection.object_detection import ObjectDetector
from src.infrastructure.adapters.video.video_manager_process import VideoSourceManager
from src.infrastructure.logging.logger import Logger
from src.infrastructure.services.object_detection_service import (
    force_default_object_data, try_capture_or_mark_for_reopen, publish_results,
)
from src.infrastructure.utils.priorities_processor import set_process_priority

def object_detection_process(object_queue,
                             shared_controls,
                             shared_frames,
                             tk_controls,
                             verbose=True,
                             camera_source=None):

    set_process_priority("high")
    manager = VideoSourceManager(camera_source)
    current_source = manager.current_source
    object_serial_data = shared_controls["OBJECT_SERIAL_DATA"]
    logger = Logger("ObjectDetection", verbose=verbose)

    safe_stop = lambda q, sc, log, reason: force_default_object_data(
        q, object_serial_data, sc, log, reason
    )

    video_proc = manager.open_video_source(
        lane_queue=object_queue,
        shared_controls=shared_controls,
        logger=logger,
        safe_stop_cb=safe_stop,
    )

    object_detector = ObjectDetector(shared_serial_data=object_serial_data,
                                     shared_frames=shared_frames,
                                     tk_controls=tk_controls,
                                     camera_source=None,
                                     logger=logger,
                                     video_processor=video_proc)

    try:
        while shared_controls.get("RUNNING", True):

            object_detector.video_processor, current_source = manager.ensure_video_source(
                video_processor=object_detector.video_processor,
                requested_source=tk_controls.get("OBJECT_SOURCE"),
                queue=object_queue,
                shared_controls=shared_controls,
                logger=logger,
                safe_stop_cb=safe_stop
            )
            if object_detector.video_processor is None:
                continue

            object_detector.video_processor, frame = try_capture_or_mark_for_reopen(
                video_proc=object_detector.video_processor,
                current_source=current_source,
                object_queue=object_queue,
                shared_controls=shared_controls,
                shared_serial_data=object_serial_data,
                logger=logger,
            )
            if frame is None:
                continue

            try:
                (
                    person_detected,
                    traffic_light_state,
                    custom_detection_state,
                ) = object_detector.process_frame(frame)
            except Exception as e:
                logger.error(f"Object detector failure: {e}")
                continue

            publish_results(
                shared_serial_data=object_serial_data,
                shared_frames=shared_frames,
                person_detected=person_detected,
                traffic_light_state=traffic_light_state,
                object_queue=object_queue,
                frame=frame,
                custom_detection_state=custom_detection_state,
            )

    except Exception as e:
        logger.error(f"Object Detection Error:{e}")
    finally:
        object_detector.cleanup()
