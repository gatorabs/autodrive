from src.infrastructure.adapters.video.video_utility_process import encode_frame

def publish(frame, shared_frames, lane_queue, lane_data, logger):
    try:
        shared_frames["TAB2_FRAME"] = encode_frame(frame)
    except Exception as e:
        logger.error(f"Erro ao codificar frames: {e}")

    if not lane_queue.full():
        lane_queue.put(lane_data)