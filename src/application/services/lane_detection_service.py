from src.infrastructure.adapters.detection.lane_detection import calculate_center_distance
import cv2 as cv

def publish(frame_display,
            edges,
            lane_queue,
            shared_frames,
            shared_controls,
            lane_data,
            fps,
            avg_time,
            logger):

    """
    Codifica quadros de exibição em JPEG, envia comandos de direção para a fila
    e atualiza a memória compartilhada com bytes de quadro e telemetria.
    """

    try:
        _, jpeg_display = cv.imencode('.jpg', frame_display)
        _, jpeg_edges   = cv.imencode('.jpg', edges)
        shared_frames["NORMAL_FRAME"] = jpeg_display.tobytes()
        shared_frames["EDGES_FRAME"]   = jpeg_edges.tobytes()
    except Exception as e:
        logger.error(f"Erro ao codificar frames: {e}")

    if not lane_queue.full():
        lane_queue.put(lane_data)

    shared_controls["CAR_INFO"]  = lane_data
    shared_controls["TIME_INFO"] = {
        'fps': round(fps, 0),
        'total_processing_time': round(avg_time, 2)
    }

def compute_distances(warped_roi, side, num_lines):
    interval = max(1, round(warped_roi.shape[0] / num_lines))
    avg_left, avg_right = calculate_center_distance(warped_roi, interval)

    lost_ref = ((side == 1 and avg_right == float('inf')) or
                (side == 0 and avg_left  == float('inf')))
    has_ref = not lost_ref

    return avg_left, avg_right, has_ref
