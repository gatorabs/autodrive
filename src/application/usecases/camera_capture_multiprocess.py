import cv2 as cv
from typing import Callable

from src.application.ports import LoggerPort, VideoSourceManager
from src.infrastructure.services.camera_capture_service import publish, camera_safe_stop

def camera_capture_process(shared_frames,
                           shared_controls,
                           tk_controls,
                           verbose=True,
                           camera_source=None,
                           logger_factory: Callable[..., LoggerPort] | None = None,
                           video_source_manager_factory: Callable[..., VideoSourceManager] | None = None,
                           priority_setter: Callable[[str], None] | None = None):

    priority_setter("above_normal")
    logger = logger_factory("CameraCapture", verbose=verbose)
    manager = video_source_manager_factory(camera_source)
    video_proc = manager.open_video_source(
        lane_queue=None,
        shared_controls=shared_controls,
        logger=logger,
        safe_stop_cb=camera_safe_stop,
    )
    current_source = manager.current_source

    if video_proc and video_proc.is_cam:
        try:
            video_proc.cap.set(cv.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass

    try:
        while shared_controls.is_running():
            requested_source = (
                tk_controls.lane_source_tab2
                if shared_controls.manual_mode
                else tk_controls.lane_source
            )
            video_proc, current_source = manager.ensure_video_source(
                video_processor=video_proc,
                requested_source=requested_source,
                queue=None,
                shared_controls=shared_controls,
                logger=logger,
                safe_stop_cb=camera_safe_stop,
            )
            if video_proc is None:
                continue

            try:
                frame = video_proc.get_frame()
                publish(
                    shared_frames=shared_frames,
                    shared_controls=shared_controls,
                    frame=frame
                )
            except RuntimeError as e:
                camera_safe_stop(None, shared_controls, logger, reason=str(e))
                try:
                    video_proc.release()
                except Exception:
                    pass
                video_proc = None

    except Exception as e:
        logger.error(f"Camera Capture Error: {e}")
    finally:
        if video_proc:
            try:
                video_proc.release()
            except Exception:
                pass
