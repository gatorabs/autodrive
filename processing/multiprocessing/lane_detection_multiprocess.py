from core import *


def lane_detection_process(lane_queue, shared_controls, video_source="test_videos/teste1.mp4"):
    set_process_priority("above_normal")
    FRAME_WIDTH = int(1920 / 4)
    FRAME_HEIGHT = int(1080 / 4)
    FRAME_CENTER = FRAME_WIDTH // 2
    ROI_START = 200
    ROI_END = 220
    ROI_X_START = 100
    ROI_X_END = 380
    NUM_LINES = 10
    TARGET_CENTER_DISTANCE = 80

    # Parâmetros do PID
    KP = 0.3
    KI = 0.005
    KD = 0.01
    MIN_OUTPUT = -32
    MAX_OUTPUT = 32

    create_control_window()

    pid = PIDController(TARGET_CENTER_DISTANCE, KP, KI, KD, MIN_OUTPUT, MAX_OUTPUT)
    lane_detector = LaneDetector(ROI_START, ROI_END)
    video_proc = VideoProcessor(video_source, FRAME_WIDTH, FRAME_HEIGHT)
    morph_kernel = cv.getStructuringElement(cv.MORPH_RECT, (4, 4))

    try:
        while True:
            frame, fps = video_proc.get_frame()
            canny_1, canny_2, speed, side = get_trackbar_values()

            # Processamento para detecção de faixas
            gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            blur = cv.GaussianBlur(gray, (5, 5), 0)
            edges = cv.Canny(blur, canny_1, canny_2)
            edges = cv.morphologyEx(edges, cv.MORPH_CLOSE, morph_kernel)

            roi = edges[ROI_START:ROI_END, ROI_X_START:ROI_X_END]
            warped_roi = bird_eye(roi)
            interval = max(1, round((ROI_END - ROI_START) / NUM_LINES))
            avg_left, avg_right = lane_detector.calculate_center_distance(warped_roi, NUM_LINES, interval)

            # Cálculo do ângulo (direção) usando PID
            direction = 0
            if side == 1:
                if avg_right != float('inf'):
                    direction = round(pid.calculate(avg_right))
            else:
                if avg_left != float('inf'):
                    direction = round(pid.calculate(avg_left))

            frame_display = draw_overlays(
                frame,
                (ROI_START, ROI_END),
                (ROI_X_START, ROI_X_END),
                (avg_left, avg_right),
                fps,
                shared_controls.get("SHOW_FPS", True),
                FRAME_CENTER
            )
            main_display = create_main_window(
                frame_display, edges, warped_roi,
                show_video=shared_controls.get("SHOW_VIDEO", True),
                show_edges=shared_controls.get("SHOW_EDGES", True),
                show_roi=shared_controls.get("SHOW_ROI", True)
            )
            cv.imshow("Lane Detection", main_display)
            if cv.waitKey(1) == ord('q'):
                break

            lane_data = {"speed": speed, "direction": direction}
            if not lane_queue.full():
                lane_queue.put(lane_data)
    except Exception as e:
        print("Lane Detection Error:", e)
    finally:
        video_proc.release()
        cv.destroyWindow("Lane Detection")
