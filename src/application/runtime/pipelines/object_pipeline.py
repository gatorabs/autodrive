from src.domain.models.data.detection_result import DetectionResult
from src.domain.models.data.object_data import ObjectData
from src.infrastructure.media.frame_codec import encode_frame


def publish_results(
    shared_serial_data,
    shared_frames,
    detection_result: DetectionResult,
    object_queue,
    frame,
    logger,
):
    object_data = detection_result.to_object_data()
    shared_serial_data[2] = object_data.object_person_data
    shared_serial_data[1] = object_data.traffic_light_data

    if len(shared_serial_data) > 0:
        shared_serial_data[0] = object_data.custom_object_data

    try:
        shared_frames.object_frame = encode_frame(frame)
    except Exception as e:
        logger.error(f"Erro ao codificar frames: {e}")

    if not object_queue.full():
        object_queue.put(object_data.to_payload())


def force_default_object_data(
    object_queue,
    shared_serial_data,
    shared_controls,
    logger,
    reason="CAMERA_ERROR",
):
    custom_serial_value = 0
    if len(shared_serial_data) > 0:
        shared_serial_data[0] = custom_serial_value
    shared_serial_data[1] = 2
    shared_serial_data[2] = 1

    object_data = ObjectData(
        object_person_data=1,
        traffic_light_data=2,
        custom_object_data=(
            shared_serial_data[0] if len(shared_serial_data) > 0 else custom_serial_value
        ),
        custom_object_label="",
    ).to_payload()
    if not object_queue.full():
        object_queue.put(object_data)

    shared_controls.object_safe_stop = True
    logger.warning(f"OBJ-SAFE-STOP ativado ({reason}).")


def try_capture_or_mark_for_reopen(
    video_proc,
    current_source,
    object_queue,
    shared_controls,
    shared_serial_data,
    logger,
):
    try:
        frame = video_proc.get_frame()
        shared_controls.object_safe_stop = False
        return video_proc, frame
    except RuntimeError as e:
        force_default_object_data(
            object_queue,
            shared_serial_data,
            shared_controls,
            logger,
            reason=str(e),
        )
        try:
            video_proc.release()
        except Exception:
            pass
        return None, None
