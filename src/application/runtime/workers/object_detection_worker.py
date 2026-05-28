from typing import Callable

from src.application.ports import LoggerPort, VideoSourceManager
from src.application.runtime.pipelines.object_pipeline import (
    force_default_object_data,
    try_capture_or_mark_for_reopen,
    publish_results,
)

def object_detection_process(object_queue,
                             shared_controls,
                             shared_frames,
                             tk_controls,
                             verbose=True,
                             camera_source=None,
                             logger_factory: Callable[..., LoggerPort] | None = None,
                             video_source_manager_factory: Callable[..., VideoSourceManager] | None = None,
                             object_detector_factory=None,
                             priority_setter: Callable[[str], None] | None = None):

    priority_setter("high")
    manager = video_source_manager_factory(camera_source)
    current_source = manager.current_source
    object_serial_data = shared_controls.object_serial_data
    logger = logger_factory("ObjectDetection", verbose=verbose)

    safe_stop = lambda q, sc, log, reason: force_default_object_data(
        q, object_serial_data, sc, log, reason
    )

    video_proc = manager.open_video_source(
        lane_queue=object_queue,
        shared_controls=shared_controls,
        logger=logger,
        safe_stop_cb=safe_stop,
    )

    object_detector = object_detector_factory(shared_serial_data=object_serial_data,
                                              shared_frames=shared_frames,
                                              tk_controls=tk_controls,
                                              camera_source=None,
                                              logger=logger,
                                              video_processor=video_proc)

    try:
        while shared_controls.is_running():

            object_detector.video_processor, current_source = manager.ensure_video_source(
                video_processor=object_detector.video_processor,
                requested_source=tk_controls.object_source,
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
                detection_result = object_detector.process_frame(frame)
            except Exception as e:
                logger.error(f"Object detector failure: {e}")
                continue

            publish_results(
                shared_serial_data=object_serial_data,
                shared_frames=shared_frames,
                detection_result=detection_result,
                object_queue=object_queue,
                frame=frame,
                logger=logger,
            )

    except Exception as e:
        logger.error(f"Object Detection Error:{e}")
    finally:
        object_detector.cleanup()
