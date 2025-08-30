import time

from src.infrastructure.adapters.video.video_utility_process import ensure_video_source_manual
from src.infrastructure.logging.logger import Logger
from src.infrastructure.services.manual_mode_service import (
    publish,
    capture_frame_with_reopen,
)
from src.infrastructure.utils.update_time_processor import update_processing_time

def manual_video_process(shared_controls, shared_frames, lane_queue):
    logger = Logger("ManualProcess")
    current_source = None
    video_proc = None

    total_processing_time = 0
    frame_count = 0

    try:
        while shared_controls.get("MANUAL_MD", False):
            start_time = time.time()
            requested_source = shared_controls.get("LANE_SOURCE_TAB2")

            video_proc, current_source = ensure_video_source_manual(
                video_processor=video_proc,
                current_source=current_source,
                requested_source=requested_source,
                logger=logger,
            )

            if video_proc is None:
                continue

            video_proc, frame = capture_frame_with_reopen(
                video_proc=video_proc,
                logger=logger,
            )

            if frame is None:
                continue

            frame_count, fps, avg_time, total_processing_time = update_processing_time(
                logger=logger,
                start_time=start_time,
                total_time=total_processing_time,
                frame_count=frame_count
            )

            publish(
                frame=frame,
                shared_frames=shared_frames,
                lane_queue=lane_queue,
                fps=fps,
                avg_time=avg_time,
                shared_controls=shared_controls,
                logger=logger
            )

    except Exception as e:
        logger.error(f"Erro no modo manual: {e}")

    finally:
        if video_proc:
            try:
                video_proc.release()
            except Exception as e:
                logger.warning(f"Erro ao liberar vídeo: {e}")
