import cv2 as cv
import time

from src.domain.constants.pid_constants import KP, KD, KI, TARGET_CENTER_DISTANCE
from src.presentation.setup_embedded_ui import draw_overlays
from src.infrastructure.adapters.video.video_utility_process import (
    toggle_named_window,
    switch_video_source,
    open_video_source,
    preprocess, ensure_video_source,
)
from src.infrastructure.logging.logger import Logger
from src.infrastructure.mappers.direction_mapper import map_direction
from src.infrastructure.services.lane_detection_service import (
    compute_distances,
    publish,
    compute_speed_and_direction,
    force_safe_stop,
    try_capture_or_mark_for_reopen,
)
from src.infrastructure.services.pid_service import (
    update_pid_from_controls,
    pid_setup,
    check_and_update_pid,
)
from src.infrastructure.utils.priorities_processor import set_process_priority
from src.infrastructure.utils.update_time_processor import update_processing_time


def lane_detection_process(lane_queue,
                           shared_controls,
                           shared_frames,
                           tk_controls,
                           verbose=True,
                           video_source=None):

    set_process_priority("above_normal")
    current_source = video_source

    logger = Logger("LaneDetection", verbose=verbose)

    last_pid_flag = shared_controls.get("NEW_PID")
    pid = pid_setup(last_pid_flag, logger)

    video_proc = open_video_source(
        current_source=current_source,
        lane_queue=lane_queue,
        shared_controls=shared_controls,
        logger=logger,
        safe_stop_cb=force_safe_stop,
    )

    morph_kernel = cv.getStructuringElement(cv.MORPH_RECT, (5, 5))

    total_processing_time = 0
    frame_count = 0
    direction = 0
    avg_time = 0
    fps = 0

    try:
        while shared_controls.get("RUNNING", True):
            start_time = time.time()

            video_proc, current_source = ensure_video_source(
                video_processor=video_proc,
                current_source=current_source,
                requested_source=tk_controls.get("LANE_SOURCE"),
                queue=lane_queue,
                shared_controls=shared_controls,
                logger=logger,
                safe_stop_cb=force_safe_stop,
            )
            if video_proc is None:
                continue

            video_proc, frame = try_capture_or_mark_for_reopen(
                video_proc=video_proc,
                current_source=current_source,
                lane_queue=lane_queue,
                shared_controls=shared_controls,
                logger=logger
            )
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

            speed, direction = compute_speed_and_direction(
                pid=pid,
                avg_left=avg_left,
                avg_right=avg_right,
                side=side,
                has_ref=has_ref,
                tk_controls=tk_controls,
                direction=direction
            )

            mapped_direction = map_direction(value=direction)

            frame_display = draw_overlays(
                frame=frame,
                distances=(avg_left, avg_right),
                warp_points=warp_points,
                edges=edges,
                has_ref=has_ref,
                mapped_direction=mapped_direction,
                show_info=tk_controls.get("SHOW_INFO"),
                show_roi_lines=tk_controls.get("SHOW_LINES"),
                fps=fps,
                ms=avg_time,
                roi=warped_roi,
                left_lines=left_lines,
                right_lines=right_lines
            )

            toggle_named_window(is_enabled=tk_controls.get("SHOW_ROI"),
                                window_name="Warped Roi",
                                frame=warped_roi)

            frame_count, fps, avg_time, total_processing_time = update_processing_time(
                logger=logger,
                start_time=start_time,
                total_time=total_processing_time,
                frame_count=frame_count)

            lane_data = {
                "CAR_SPEED_DATA": speed,
                "CAR_DIRECTION_DATA": mapped_direction
                         }

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
        video_proc.release()
        cv.destroyAllWindows()
