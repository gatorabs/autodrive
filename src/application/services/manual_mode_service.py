import cv2

def publish(frame, shared_frames, lane_queue, lane_data, logger):
    try:
        _, buffer = cv2.imencode('.jpg', frame)
        shared_frames["TAB2_FRAME"] = buffer.tobytes()
    except Exception as e:
        logger.error(f"Erro ao codificar frames: {e}")

    if not lane_queue.full():
        lane_queue.put(lane_data)