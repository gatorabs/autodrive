from core import *
from processing.warp_perspective_processor import create_track


def lane_detection_process(lane_queue, shared_controls, shared_frames, video_source="test_videos/teste1.mp4"):
    set_process_priority("above_normal")
    FRAME_WIDTH = int(1920 / 4)
    FRAME_HEIGHT = int(1080 / 4)
    FRAME_CENTER = FRAME_WIDTH // 2

    NUM_LINES = 10
    TARGET_CENTER_DISTANCE = 125

    '''
    Ki (ganho integral)
    
    Reduz o offset em regime permanente, mas se for muito alto causa windup, acumulando erro demais.
    Solução: diminuir o valor de ki (ou então implementar/fortalecer o anti-windup, limitando ainda mais self.integral).

    Kp (ganho proporcional)
    Dá resposta imediata ao erro atual. Aumentar Kp faz a correção ser mais rápida, mas também pode gerar oscilações.

    Kd (ganho derivativo)
    “Frena” a resposta baseada na taxa de variação do erro, ajudando a amortecer oscilações e reduzir sobre-impulsos.
    
    '''
    
    # Parâmetros do PID
    KP = 0.3
    KI = 0.003
    KD = 0.015
    MIN_OUTPUT = -32
    MAX_OUTPUT = 32

    create_control_window()
    create_track()
    create_roi_trackbars("ROI_C", FRAME_WIDTH,FRAME_HEIGHT)

    pid = PIDController(TARGET_CENTER_DISTANCE, KP, KI, KD, MIN_OUTPUT, MAX_OUTPUT)
    video_proc = VideoProcessor(video_source, FRAME_WIDTH, FRAME_HEIGHT)
    morph_kernel = cv.getStructuringElement(cv.MORPH_RECT, (4, 4))

    try:
        while shared_controls.get("RUNNING", True):
            frame, fps = video_proc.get_frame()
            canny_1, canny_2, speed, side, kp, ki, kd = get_control_trackbar_values()

            ROI_START, ROI_END, ROI_X_START, ROI_X_END = \
                get_roi_trackbars(FRAME_WIDTH, FRAME_HEIGHT)

            #pid.kp = kp <- Para teste de valores
            #pid.ki = ki
            #pid.kd = kd

            # Processamento para detecção de faixas
            gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            blur = cv.GaussianBlur(gray, (5, 5), 0)
            edges = cv.Canny(blur, canny_1, canny_2)
            edges = cv.morphologyEx(edges, cv.MORPH_CLOSE, morph_kernel)

            roi = edges[ROI_START:ROI_END, ROI_X_START:ROI_X_END]
            warped_roi = bird_eye(roi)
            interval = max(1, round((ROI_END - ROI_START) / NUM_LINES))
            avg_left, avg_right = calculate_center_distance(warped_roi, interval)

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

            def mouse_callback(event, x, y, flags, param):
                if event == cv.EVENT_LBUTTONDOWN:
                    print(f"Coordenadas: x={x}, y={y}")

            cv.namedWindow("Inspecionar")
            cv.setMouseCallback("Inspecionar", mouse_callback)
            cv.imshow("Inspecionar", roi)

            cv.namedWindow("Tesste")

            cv.imshow("Tesste", warped_roi)




            try:
                _, jpeg_display = cv.imencode('.jpg', frame_display)
                _, jpeg_edges = cv.imencode('.jpg', edges)
                _, jpeg_warped = cv.imencode('.jpg', warped_roi)

                shared_frames["display"] = jpeg_display.tobytes()
                shared_frames["edges"] = jpeg_edges.tobytes()
                shared_frames["warped"] = jpeg_warped.tobytes()
            except Exception as e:
                print("Erro ao codificar frames:", e)

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
        cv.destroyAllWindows()
