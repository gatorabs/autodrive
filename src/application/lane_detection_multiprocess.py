
from src.core.__init__lane import *


def lane_detection_process(lane_queue,
                           shared_controls,
                           shared_frames,
                           tk_controls,
                           verbose=True,
                           video_source="test_videos/pista_01.mp4"):

    set_process_priority("above_normal")

    TARGET_CENTER_DISTANCE = 80
    logger = Logger("LaneDetection", verbose=verbose)

    # PID parâmetros
    KP = 0.3
    KI = 0.003
    KD = 0.015
    MIN_OUTPUT = -32
    MAX_OUTPUT = 32

    direction = 0

    def map_direction(value, in_min=-32, in_max=32, out_min=0, out_max=180):
        return int((value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

    def make_pid(use_new: bool):
        cls = PIDV2Controller if use_new else PIDController
        return cls(set_point=TARGET_CENTER_DISTANCE,
                   kp=KP, ki=KI, kd=KD,
                   min_output=MIN_OUTPUT, max_output=MAX_OUTPUT,
                   logger=logger)

    pid = make_pid(shared_controls.get("NEW_PID"))

    video_proc = VideoProcessor(video_source=video_source,
                                frame_width=FRAME_WIDTH,
                                frame_height=FRAME_HEIGHT)

    morph_kernel = cv.getStructuringElement(cv.MORPH_RECT, (4, 4))

    total_processing_time = 0
    frame_count = 0

    try:
        while shared_controls.get("RUNNING", True):
            start_time = time.time()

            canny_1 = tk_controls.get("F_Canny")
            canny_2 = tk_controls.get("S_Canny")
            side = tk_controls.get("Side", 1)
            num_lines = tk_controls.get("Lines", 10)

            pid.set_point = tk_controls.get("Distance", TARGET_CENTER_DISTANCE)
            pid.kp = tk_controls.get("KP", KP)
            pid.ki = tk_controls.get("KI", KI)
            pid.kd = tk_controls.get("KD", KD)

            frame = video_proc.get_frame()
            if frame is None:
                logger.error(f"Frame não capturado. Cheque o vídeo ou câmera.")
                break

            logger.verbose = tk_controls.get("LANE_LOGS")

            gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            blur = cv.GaussianBlur(gray, (5, 5), 0)
            edges = cv.Canny(blur, canny_1, canny_2)
            edges = cv.morphologyEx(edges, cv.MORPH_CLOSE, morph_kernel)

            try:
                warp_points = get_warp_points_from_controls(tk_controls)
                warped_roi = bird_eye_full(edges, warp_points, draw_on=frame)
            except cv.error as e:
                logger.error(f"Erro no warpPerspective: {e}")
                continue

            interval = max(1, round(warped_roi.shape[0] / num_lines))
            avg_left, avg_right = calculate_center_distance(warped_roi, interval)

            lost_ref = (side == 1 and avg_right == float('inf')) or \
                       (side == 0 and avg_left == float('inf'))

            has_ref = not lost_ref

            if lost_ref:
                speed = 0
            else:
                speed = tk_controls.get("Speed")

                if side == 1:
                    direction = round(pid.calculate(avg_right))
                else:
                    direction = round(pid.calculate(avg_left))

            mapped_direction = map_direction(direction)

            frame_display = draw_overlays(
                frame=frame,
                distances=(avg_left, avg_right),
                warp_points=warp_points,
                edges=edges,
                has_ref=has_ref,
                mapped_direction=mapped_direction
            )

            try:
                _, jpeg_display = cv.imencode('.jpg', frame_display)
                _, jpeg_edges = cv.imencode('.jpg', edges)
                shared_frames["display"] = jpeg_display.tobytes()
                shared_frames["edges"] = jpeg_edges.tobytes()
            except Exception as e:
                logger.error(f"Erro ao codificar frames: {e}")

            lane_data = {"speed": speed, "direction": mapped_direction}

            if not lane_queue.full():
                lane_queue.put(lane_data)

            frame_count, fps, avg_time, total_processing_time = update_processing_time(
                logger, start_time, total_processing_time, frame_count)

            shared_controls["car_info"] = lane_data
            shared_controls["time_info"] = {
                "fps": round(fps, 0),
                "total_processing_time": round(avg_time, 2)
            }

            if tk_controls.get("SHOW_ROI", False):
                cv.imshow("warped", warped_roi)
            else:
                try:
                    if cv.getWindowProperty("warped", cv.WND_PROP_VISIBLE) >= 1:
                        cv.destroyWindow("warped")
                except cv.error:
                    pass

            if cv.waitKey(1) == ord('q'):
                break

    except Exception as e:
        logger.error(f"Lane Detection Error: {e}")

    finally:
        video_proc.release()
        cv.destroyAllWindows()