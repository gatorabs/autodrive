import cv2 as cv
import time
from typing import Callable

from src.application.ports import LoggerPort
from src.application.monitoring.frame_timing import update_processing_time
from src.domain.constants.pid_constants import KP, KD, KI, TARGET_CENTER_DISTANCE
from src.application.services.lane_pipeline import (
    compute_distances,
    publish,
    compute_speed_and_direction,
    define_and_calculate_side,
    apply_speed_override,
    preprocess,
)
from src.application.services.pid_factory import (
    update_pid_from_controls,
    pid_setup,
    check_and_update_pid,
)
from src.domain.models.data.lane_data import LaneData
from src.infrastructure.vision.opencv_windows import toggle_named_window


def lane_detection_process(lane_queue,
                           shared_controls,
                           shared_frames,
                           tk_controls,
                           overlay_renderer,
                           logger_factory: Callable[..., LoggerPort],
                           priority_setter: Callable[[str], None],
                           verbose=True):

    priority_setter("above_normal")

    logger = logger_factory("LaneDetection", verbose=verbose)

    last_pid_flag = shared_controls.get("NEW_PID")
    pid = pid_setup(last_pid_flag, logger)

    morph_kernel = cv.getStructuringElement(cv.MORPH_RECT, (5, 5))

    total_processing_time = 0
    frame_count = 0
    direction = 0
    avg_time = 0
    fps = 0

    try:
        while shared_controls.is_running():
            start_time = time.time()
            if shared_controls.safe_stop:
                continue
            frame = shared_frames.camera_frame
            if frame is None:
                continue

            try:
                (edges,
                 warp_points,
                 warped_roi,
                 side,
                 num_lines,
                 max_height) = preprocess(frame=frame,
                                          tk_controls=tk_controls,
                                          morph_kernel=morph_kernel)
            except cv.error as e:
                logger.error(f"Erro no preprocess: {e}")
                continue

            (avg_left,
             avg_right,
             has_ref,
             left_lines,
             right_lines) = compute_distances(
                warped_roi=warped_roi,
                side=side,
                num_lines=num_lines)

            pid, last_pid_flag = check_and_update_pid(pid=pid,
                                                      last_pid_flag=last_pid_flag,
                                                      shared_controls=shared_controls,
                                                      logger=logger)

            update_pid_from_controls(
                pid=pid,
                controls=tk_controls,
                default_set_point=TARGET_CENTER_DISTANCE,
                default_kp=KP, default_ki=KI, default_kd=KD
            )

            speed, direction, side = compute_speed_and_direction(
                pid=pid,
                avg_left=avg_left,
                avg_right=avg_right,
                side=side,
                has_ref=has_ref,
                tk_controls=tk_controls,
                direction=direction,
                shared_controls=shared_controls,
            )

            speed = apply_speed_override(shared_controls=shared_controls,
                                         tk_controls=tk_controls, current_speed=speed)

            mapped_direction = define_and_calculate_side(direction=direction,
                                                         side=side)

            frame_display = overlay_renderer(
                frame=frame,
                distances=(avg_left, avg_right),
                warp_points=warp_points,
                edges=edges,
                has_ref=has_ref,
                mapped_direction=mapped_direction,
                show_info=tk_controls.show_info,
                show_roi_lines=tk_controls.show_lines,
                fps=fps,
                ms=avg_time,
                roi=warped_roi,
                left_lines=left_lines,
                right_lines=right_lines,
                distance_value=tk_controls.distance
            )

            toggle_named_window(is_enabled=tk_controls.show_roi,
                                window_name="Warped Roi",
                                frame=warped_roi)

            frame_count, fps, avg_time, total_processing_time = update_processing_time(
                logger=logger,
                start_time=start_time,
                total_time=total_processing_time,
                frame_count=frame_count)

            lane_data = LaneData(
                car_speed_data=speed,
                car_direction_data=mapped_direction,
            ).to_payload()

            publish(
                frame_display=frame_display,
                edges=edges,
                lane_queue=lane_queue,
                shared_frames=shared_frames,
                shared_controls=shared_controls,
                lane_data=lane_data,
                fps=fps,
                avg_time=avg_time,
                max_height=max_height,
                logger=logger
            )

            if cv.waitKey(1) == ord('q'):
                break

    except Exception as e:
        logger.error(f"Lane Detection Error: {e}")

    finally:
        cv.destroyAllWindows()
