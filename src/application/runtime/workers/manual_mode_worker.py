import time
from typing import Callable

from src.application.runtime.monitoring.frame_timing import update_processing_time
from src.application.ports import LoggerPort
from src.application.runtime.pipelines.manual_mode_pipeline import publish


def manual_video_process(
    shared_controls,
    shared_frames,
    lane_queue,
    logger_factory: Callable[..., LoggerPort],
):
    logger = logger_factory("ManualProcess")

    total_processing_time = 0
    frame_count = 0

    try:
        while shared_controls.manual_mode:
            start_time = time.time()
            frame = shared_frames.camera_frame
            if frame is None:
                continue

            frame_count, fps, avg_time, total_processing_time = update_processing_time(
                logger=logger,
                start_time=start_time,
                total_time=total_processing_time,
                frame_count=frame_count,
            )

            publish(
                frame=frame,
                shared_frames=shared_frames,
                lane_queue=lane_queue,
                fps=fps,
                avg_time=avg_time,
                shared_controls=shared_controls,
                logger=logger,
            )

    except Exception as e:
        logger.error(f"Erro no modo manual: {e}")
