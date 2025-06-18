import cv2
from core import *
from utils.constants import RED, RESET, YELLOW, GREEN
from processing.update_time_processor import update_processing_time

def lane_detection_process(lane_queue, shared_controls, shared_frames, tk_controls,
                           video_source="test_videos/pista_01.mov"):
    set_process_priority("above_normal")

    FRAME_WIDTH = int(1920 / 4)
    FRAME_HEIGHT = int(1080 / 4)
    FRAME_CENTER = FRAME_WIDTH // 2

    NUM_LINES = 10
    TARGET_CENTER_DISTANCE = 80

    # PID parâmetros
    KP = 0.3
    KI = 0.003
    KD = 0.015
    MIN_OUTPUT = -32
    MAX_OUTPUT = 32

    direction = 0

    def map_direction(value, in_min=-32, in_max=32, out_min=0, out_max=180):
        return int((value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

    webview = shared_controls.get("WEBVIEW")

    pid = PIDController(TARGET_CENTER_DISTANCE, KP, KI, KD, MIN_OUTPUT, MAX_OUTPUT)
    video_proc = VideoProcessor(video_source, FRAME_WIDTH, FRAME_HEIGHT)
    morph_kernel = cv.getStructuringElement(cv.MORPH_RECT, (4, 4))

    total_processing_time = 0
    frame_count = 0

    try:
        while shared_controls.get("RUNNING", True):
            start_time = time.time()

            frame = video_proc.get_frame()
            if frame is None:
                print(f"{RED}[ERROR]{RESET} Frame não capturado. Cheque o vídeo ou câmera.")
                break

            canny_1 = tk_controls.get("F_Canny", 50)
            canny_2 = tk_controls.get("S_Canny", 150)
            speed = tk_controls.get("Speed", 50)
            side = tk_controls.get("Side", 1)

            ROI_START = tk_controls.get("ROI_START", 0)
            ROI_END = tk_controls.get("ROI_END", FRAME_HEIGHT)
            ROI_X_START = tk_controls.get("ROI_X_START", 0)
            ROI_X_END = tk_controls.get("ROI_X_END", FRAME_WIDTH)

            ROI_START = max(0, min(ROI_START, FRAME_HEIGHT - 1))
            ROI_END = max(ROI_START + 10, min(ROI_END, FRAME_HEIGHT))

            ROI_X_START = max(0, min(ROI_X_START, FRAME_WIDTH - 1))
            ROI_X_END = max(ROI_X_START + 10, min(ROI_X_END, FRAME_WIDTH))

            gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            blur = cv.GaussianBlur(gray, (5, 5), 0)
            edges = cv.Canny(blur, canny_1, canny_2)
            edges = cv.morphologyEx(edges, cv.MORPH_CLOSE, morph_kernel)


            try:
                warp_points = get_warp_points_from_controls(tk_controls)
                warped_roi = bird_eye_full(edges, warp_points, draw_on=frame)
            except cv.error as e:
                print(f"{RED}[ERROR]{RESET} Erro no warpPerspective: {e}")
                continue

            interval = max(1, round(warped_roi.shape[0] / NUM_LINES))   
            avg_left, avg_right = calculate_center_distance(warped_roi, interval)

            if side == 1 and avg_right != float('inf'):
                direction = round(pid.calculate(avg_right))
            elif side == 0 and avg_left != float('inf'):
                direction = round(pid.calculate(avg_left))

            frame_display = draw_overlays(
                frame,
                (ROI_START, ROI_END),
                (ROI_X_START, ROI_X_END),
                (avg_left, avg_right),
                FRAME_CENTER, warp_points,edges
            )

            if webview:
                try:
                    _, jpeg_display = cv.imencode('.jpg', frame_display)
                    _, jpeg_edges = cv.imencode('.jpg', edges)
                    shared_frames["display"] = jpeg_display.tobytes()
                    shared_frames["edges"] = jpeg_edges.tobytes()
                except Exception as e:
                    print(f"{RED}[ERROR]{RESET} Erro ao codificar frames: {e}")
            else:
                main_display = create_main_window(
                    frame_display, edges, warped_roi,
                    show_video=tk_controls.get("SHOW_VIDEO", True),
                    show_edges=tk_controls.get("SHOW_EDGES", True),
                    show_roi=tk_controls.get("SHOW_ROI", True)
                )
                cv.imshow("Lane Detection", main_display)

            if cv.waitKey(1) == ord('q'):
                break

            mapped_direction = map_direction(direction)

            lane_data = {"speed": speed, "direction": mapped_direction}

            if not lane_queue.full():
                lane_queue.put(lane_data)

            frame_count, fps, avg_time, total_processing_time = update_processing_time(
                shared_controls, start_time, total_processing_time, frame_count)

            shared_controls["car_info"] = lane_data
            shared_controls["time_info"] = {
                "fps": round(fps, 0),
                "total_processing_time": round(avg_time, 2)
            }

            cv.imshow("warped", warped_roi)

    except Exception as e:
        print(f"{YELLOW}[LaneDetection]{RED}[ERROR] Lane Detection Error: {e}{RESET}")

    finally:
        video_proc.release()
        cv.destroyAllWindows()