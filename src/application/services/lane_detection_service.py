from src.infrastructure.adapters.detection.lane_detection import calculate_center_distance
import cv2 as cv
import numpy as np

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
    # guard against zero or negative number of lines to avoid division by zero
    if num_lines <= 0:
        interval = 1
    else:
        interval = max(1, round(warped_roi.shape[0] / num_lines))
    avg_left, avg_right = calculate_center_distance(warped_roi, interval)

    lost_ref = ((side == 1 and avg_right == float('inf')) or
                (side == 0 and avg_left  == float('inf')))
    has_ref = not lost_ref

    return avg_left, avg_right, has_ref

def get_warp_points_from_controls(ctrl):
    return (
        ctrl["tl_x"], ctrl["tl_y"],
        ctrl["tr_x"], ctrl["tr_y"],
        ctrl["bl_x"], ctrl["bl_y"],
        ctrl["br_x"], ctrl["br_y"]
    )

def bird_eye_full(frame, warp_points, draw_on=None):
    h, w = frame.shape[:2]

    tl_x, tl_y, tr_x, tr_y, bl_x, bl_y, br_x, br_y = warp_points

    tl = (tl_x, tl_y)
    tr = (tr_x, tr_y)
    bl = (bl_x, bl_y)
    br = (br_x, br_y)

    if draw_on is not None:
        for pt in [tl, tr, bl, br]:
            cv.circle(draw_on, pt, 4, (255, 0, 0), -1)

    # Define a largura e altura da nova perspectiva baseada na distância entre pontos
    width_top = np.linalg.norm(np.array(tr) - np.array(tl))
    width_bottom = np.linalg.norm(np.array(br) - np.array(bl))
    height_left = np.linalg.norm(np.array(bl) - np.array(tl))
    height_right = np.linalg.norm(np.array(br) - np.array(tr))

    max_width = int(max(width_top, width_bottom))
    max_height = int(max(height_left, height_right))

    # Pontos de origem e destino
    pts1 = np.float32([tl, bl, tr, br])
    pts2 = np.float32([
        [0, 0],
        [0, max_height],
        [max_width, 0],
        [max_width, max_height]
    ])

    M = cv.getPerspectiveTransform(pts1, pts2)
    warped = cv.warpPerspective(frame, M, (max_width, max_height))

    return warped
