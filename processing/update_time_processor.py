import time
from extensions.constants.colorsConstants import YELLOW, GREEN, RESET

def update_processing_time(logger, start_time, total_time, frame_count, log_interval=100):
    end_time = time.time()
    frame_time = (end_time - start_time) * 1000  # em milissegundos
    total_time += frame_time
    frame_count += 1

    fps = 1.0 / (end_time - start_time) if (end_time - start_time) > 0 else 0.0
    avg_time = total_time / frame_count
    if frame_count % log_interval == 0:
        logger.info(
            f"Tempo médio por frame: {avg_time:.2f} ms (baseado em {frame_count} frames)")
        logger.info(
            f"FPS: {fps:.2f}."
        )
    return frame_count, fps, avg_time, total_time

