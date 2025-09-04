def publish(shared_frames, shared_controls, frame):
    shared_frames["CAMERA_FRAME"] = frame
    shared_controls["SAFE_STOP"] = False

def camera_safe_stop(_, shared_controls, logger, reason="CAMERA_ERROR"):
    shared_controls["SAFE_STOP"] = True
    logger.warning(f"SAFE-STOP ativado ({reason}).")