from src.infrastructure.utils.frame_utils import encode_frame

def publish(frame,
            shared_frames,
            lane_queue,
            logger,
            fps,
            avg_time,
            shared_controls):
    try:
        shared_frames["TAB2_FRAME"] = encode_frame(frame)
    except Exception as e:
        logger.error(f"Erro ao codificar frames: {e}")

    if not lane_queue.full():
        lane_queue.put(shared_controls["CAR_INFO"])

    shared_controls["TIME_INFO"] = {
        'fps': round(fps, 0),
        'total_processing_time': round(avg_time, 2)
    }


def capture_frame_with_reopen(video_proc, logger):
    """Tenta capturar um frame; em caso de falha libera a fonte para reabertura."""
    try:
        frame = video_proc.get_frame()
        return video_proc, frame
    except RuntimeError as e:
        logger.warning(f"Erro ao capturar frame: {e}")
        try:
            video_proc.release()
        except Exception:
            pass
        return None, None
