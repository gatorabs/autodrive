from src.core.__init__lane import *


def lane_detection_process(lane_queue,
                           shared_controls,
                           shared_frames,
                           tk_controls,
                           verbose=True,
                           video_source=None):

    set_process_priority("above_normal")
    current_source = video_source

    logger = Logger("LaneDetection", verbose=verbose)


    pid = pid_setup(shared_controls.get("NEW_PID"), logger)

    video_proc = VideoProcessor(video_source=current_source,
                                frame_width=FRAME_WIDTH,
                                frame_height=FRAME_HEIGHT)

    morph_kernel = cv.getStructuringElement(cv.MORPH_RECT, (5, 5))

    total_processing_time = 0
    frame_count = 0
    direction = 0
    fps = 0

    try:
        while shared_controls.get("RUNNING", True):
            start_time = time.time()

            new_source = tk_controls.get("LANE_SOURCE")
            video_proc, current_source = switch_video_source(
                video_processor=video_proc,
                current_source=current_source,
                new_source=new_source,
                logger=logger
            )

            logger.verbose = tk_controls.get("LANE_LOGS")

            frame = video_proc.get_frame()
            if frame is None:
                logger.error(f"Frame não capturado. Cheque o vídeo ou câmera.")
                break

            try:
                (edges,
                 warp_points,
                 warped_roi,
                 side,
                 num_lines) = preprocess(frame=frame,
                                         tk_controls=tk_controls,
                                         morph_kernel=morph_kernel)
            except cv.error as e:
                logger.error(f"Erro no preprocess: {e}")
                continue

            avg_left, avg_right, has_ref = compute_distances(warped_roi=warped_roi,
                                                             side=side,
                                                             num_lines=num_lines)

            update_pid_from_controls(
                pid=pid,
                controls=tk_controls,
                default_set_point=TARGET_CENTER_DISTANCE,
                default_kp=KP, default_ki=KI, default_kd=KD
            )

            if has_ref:
                speed = tk_controls.get("Speed")

                if side == 1:
                    direction = round(pid.calculate(avg_right))
                else:
                    direction = round(pid.calculate(avg_left))
            else:
                speed = 0

            mapped_direction = map_direction(value=direction)

            lane_data = {
                "CAR_SPEED_DATA": speed,
                "CAR_DIRECTION_DATA": mapped_direction
                         }

            frame_display = draw_overlays(
                frame=frame,
                distances=(avg_left, avg_right),
                warp_points=warp_points,
                edges=edges,
                has_ref=has_ref,
                mapped_direction=mapped_direction,
                show_info=tk_controls.get("SHOW_INFO"),
                fps=fps
            )

            toggle_named_window(is_enabled=tk_controls.get("SHOW_ROI"),
                                window_name="Warped Roi",
                                frame=warped_roi)

            frame_count, fps, avg_time, total_processing_time = update_processing_time(
                logger=logger,
                start_time=start_time,
                total_time=total_processing_time,
                frame_count=frame_count)

            publish(
                frame_display=frame_display,
                edges=edges,
                lane_queue=lane_queue,
                shared_frames=shared_frames,
                shared_controls=shared_controls,
                lane_data=lane_data,
                fps=fps,
                avg_time=avg_time,
                logger=logger
            )

            if cv.waitKey(1) == ord('q'):
                break

    except Exception as e:
        logger.error(f"Lane Detection Error: {e}")

    finally:
        video_proc.release()
        cv.destroyAllWindows()