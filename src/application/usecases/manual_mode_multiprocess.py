import time

from src.infrastructure.logging.logger import Logger
from src.infrastructure.services.manual_mode_service import publish
from src.infrastructure.utils.update_time_processor import update_processing_time


def manual_video_process(shared_controls, shared_frames, lane_queue):
    logger = Logger("ManualProcess")

    total_processing_time = 0
    frame_count = 0

    try:
        while shared_controls.get("MANUAL_MD", False):
            start_time = time.time()
            frame = shared_frames.get("CAMERA_FRAME")
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
