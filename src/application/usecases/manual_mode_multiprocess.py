import time

from src.infrastructure.adapters.video.video_utility_process import switch_video_source
from src.infrastructure.logging.logger import Logger
from src.infrastructure.services.manual_mode_service import publish
from src.infrastructure.utils.update_time_processor import update_processing_time

def manual_video_process(shared_controls, shared_frames, lane_queue):
    logger = Logger("ManualProcess")
    current_source = None
    video_proc = None

    total_processing_time = 0
    frame_count = 0
    avg_time = 0
    fps = 0

    try:
        while shared_controls.get("MANUAL_MD", False):
            start_time = time.time()
            new_source = shared_controls.get("LANE_SOURCE_TAB2")

            video_proc, current_source = switch_video_source(
                video_processor=video_proc,
                current_source=current_source,
                new_source=new_source,
                logger=logger
            )

            frame = video_proc.get_frame()
            if frame is None:
                logger.error("Frame não capturado. Cheque o vídeo ou câmera.")
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
