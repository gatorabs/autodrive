import time
from utils.constants import YELLOW,GREEN,RESET

def update_processing_time(start_time, total_time, frame_count, log_interval=100):
    end_time = time.time()
    frame_time = (end_time - start_time) * 1000  # em milissegundos
    total_time += frame_time
    frame_count += 1

    if frame_count % log_interval == 0:
        avg_time = total_time / frame_count
        print(
            f"{YELLOW}[LaneDetection]{GREEN}[INFO] Tempo médio por frame: {avg_time:.2f} ms (baseado em {frame_count} frames){RESET}")

    return total_time