from src.infrastructure.adapters.detection.lane_detection import calculate_center_distance

def compute_distances(warped_roi, side, num_lines):

    # calcula o intervalo entre linhas de análise
    interval = max(1, round(warped_roi.shape[0] / num_lines))
    # função existente que retorna (avg_left, avg_right)
    avg_left, avg_right = calculate_center_distance(warped_roi, interval)

    lost_ref = ((side == 1 and avg_right == float('inf')) or
                (side == 0 and avg_left  == float('inf')))
    has_ref = not lost_ref

    return avg_left, avg_right, has_ref