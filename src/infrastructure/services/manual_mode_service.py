from src.infrastructure.utils.frame_utils import encode_frame

def publish(frame,
            shared_frames,
            lane_queue,
            logger,
            fps,
            avg_time,
            shared_controls):
    try:
        shared_frames.tab2_frame = encode_frame(frame)
    except Exception as e:
        logger.error(f"Erro ao codificar frames: {e}")

    if not lane_queue.full():
        lane_queue.put(shared_controls.car_info)

    shared_controls.set_time_info(fps, avg_time)


def capture_frame_with_reopen(video_proc, logger):
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
