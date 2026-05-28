from src.infrastructure.adapters.video.video_capture import VideoCapture
from src.infrastructure.media.frame_codec import encode_frame

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


def ensure_video_source_manual(video_processor, current_source, requested_source, logger):
    desired_source = requested_source if requested_source is not None else current_source

    if desired_source is None:
        logger.error("Nenhuma fonte definida para abrir/trocar.")
        return None, current_source

    if video_processor is None or not video_processor.is_frame_open():
        try:
            vp = VideoCapture(video_source=desired_source)
            logger.info(f"Fonte aberta: {desired_source}")
            return vp, desired_source
        except Exception as e:
            logger.error(f"Falha ao abrir fonte {desired_source}: {e}")
            return None, current_source

    if desired_source != current_source:
        logger.info(f"Trocando Source de {current_source} para {desired_source}")
        try:
            new_vp = VideoCapture(video_source=desired_source)
        except Exception as e:
            logger.error(f"Falha ao trocar para fonte {desired_source}: {e}")

            if video_processor.is_frame_open():
                return video_processor, current_source
            return None, current_source

        try:
            video_processor.release()
        except Exception:
            pass
        return new_vp, desired_source

    return video_processor, current_source
