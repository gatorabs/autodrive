import cv2 as cv

def publish(
    frame_display,
    edges,
    lane_queue,
    shared_frames,
    shared_controls,
    lane_data,
    fps,
    avg_time,
    logger
):
    """
    Encodes display frames to JPEG, pushes driving commands to the queue,
    and updates shared memory with frame bytes and telemetry.
    """

    try:
        _, jpeg_display = cv.imencode('.jpg', frame_display)
        _, jpeg_edges   = cv.imencode('.jpg', edges)
        shared_frames['display'] = jpeg_display.tobytes()
        shared_frames['edges']   = jpeg_edges.tobytes()
    except Exception as e:
        logger.error(f"Erro ao codificar frames: {e}")

    if not lane_queue.full():
        lane_queue.put(lane_data)

    shared_controls['car_info']  = lane_data
    shared_controls['time_info'] = {
        'fps': round(fps, 0),
        'total_processing_time': round(avg_time, 2)
    }
