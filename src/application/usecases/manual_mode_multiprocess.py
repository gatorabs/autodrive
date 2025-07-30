from src.core.__init__manual import *

def manual_video_process(shared_controls, shared_frames, lane_queue):
    logger = Logger("ManualProcess")
    current_source = None
    video_proc = None

    try:
        while shared_controls.get("MANUAL_MD", False):
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

            publish(frame=frame,
                    shared_frames=shared_frames,
                    lane_queue=lane_queue,
                    lane_data=shared_controls["CAR_INFO"],
                    logger=logger)

    except Exception as e:
        logger.error(f"Erro no modo manual: {e}")

    finally:
        if video_proc:
            try:
                video_proc.release()
            except Exception as e:
                logger.warning(f"Erro ao liberar vídeo: {e}")