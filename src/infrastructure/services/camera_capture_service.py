def publish(shared_frames, shared_controls, frame):
    shared_frames.camera_frame = frame
    shared_controls.safe_stop = False

def camera_safe_stop(_, shared_controls, logger, reason="CAMERA_ERROR"):
    shared_controls.safe_stop = True
    logger.warning(f"SAFE-STOP ativado ({reason}).")
