import time
from extensions.constants.colorsConstants import YELLOW, GREEN, RESET

def update_processing_time(shared_controls, start_time, total_time, frame_count, log_interval=100):
    end_time = time.time()
    frame_time = (end_time - start_time) * 1000  # em milissegundos
    total_time += frame_time
    frame_count += 1

    fps = 1.0 / (end_time - start_time) if (end_time - start_time) > 0 else 0.0
    avg_time = total_time / frame_count
    if frame_count % log_interval == 0:
        print(
            f"{YELLOW}[LaneDetection]{GREEN}[INFO] Tempo médio por frame: {avg_time:.2f} ms (baseado em {frame_count} frames){RESET}")
        print(
            f"{YELLOW}[LaneDetection]{GREEN}[INFO] FPS: {fps:.2f}.{RESET}"
        )
    return frame_count, fps, avg_time, total_time

