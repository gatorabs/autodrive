import cv2

from core import *
from utils.constants import RED,RESET,YELLOW, GREEN
from processing.update_time_processor import update_processing_time

def lane_detection_process(lane_queue, shared_controls, shared_frames, video_source="test_videos/pista_01 (1).mov"):

    set_process_priority("above_normal")
    FRAME_WIDTH = int(1920 / 4)
    FRAME_HEIGHT = int(1080 / 4)
    FRAME_CENTER = FRAME_WIDTH // 2

    NUM_LINES = 10
    TARGET_CENTER_DISTANCE = 80

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

    direction = 0

    def map_direction(value, in_min=-32, in_max=32, out_min=0, out_max=180):
        return int((value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

    create_control_window()
    webview = shared_controls.get("WEBVIEW")
    CALIBRATE_ROI = False

    if webview:
        CALIBRATE_ROI = False
    else:
        if CALIBRATE_ROI:
            create_warp_points_trackbars()

    create_roi_trackbars("ROI_C", FRAME_WIDTH, FRAME_HEIGHT)

    pid = PIDController(TARGET_CENTER_DISTANCE, KP, KI, KD, MIN_OUTPUT, MAX_OUTPUT)
    video_proc = VideoProcessor(video_source, FRAME_WIDTH, FRAME_HEIGHT)
    morph_kernel = cv.getStructuringElement(cv.MORPH_RECT, (4, 4))

    # Variáveis para medir eficiência
    total_processing_time = 0
    frame_count = 0

    try:
        while shared_controls.get("RUNNING", True):
            start_time = time.time()

            frame = video_proc.get_frame()
            canny_1, canny_2, speed, side, kp, ki, kd = get_control_trackbar_values()

            # pid.kp = kp <- Para teste de valores
            # pid.ki = ki
            # pid.kd = kd

            ROI_START, ROI_END, ROI_X_START, ROI_X_END = get_roi_trackbars(FRAME_WIDTH, FRAME_HEIGHT)

            # Processamento para detecção de faixas
            gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            blur = cv.GaussianBlur(gray, (5, 5), 0)
            edges = cv.Canny(blur, canny_1, canny_2)
            edges = cv.morphologyEx(edges, cv.MORPH_CLOSE, morph_kernel)

            roi = edges[ROI_START:ROI_END, ROI_X_START:ROI_X_END]

            warped_roi = bird_eye(roi, CALIBRATE_ROI)
            interval = max(1, round((ROI_END - ROI_START) / NUM_LINES))
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
                FRAME_CENTER
            )

            # Função para Descobrir Pixel atual:

            # def mouse_callback(event, x, y, flags, param):
            #    if event == cv.EVENT_LBUTTONDOWN:
            #        print(f"Coordenadas: x={x}, y={y}")

            # cv.namedWindow("Inspecionar")
            # cv.setMouseCallback("Inspecionar", mouse_callback)
            # cv.imshow("Inspecionar", roi)

            # WEBVIEW ativo → envia para o front
            if webview:
                try:
                    _, jpeg_display = cv.imencode('.jpg', frame_display)
                    _, jpeg_edges = cv.imencode('.jpg', edges)
                    shared_frames["display"] = jpeg_display.tobytes()
                    shared_frames["edges"] = jpeg_edges.tobytes()
                except Exception as e:
                    print("Erro ao codificar frames:", e)
            else:
                main_display = create_main_window(
                    frame_display, edges, warped_roi,
                    show_video=shared_controls.get("SHOW_VIDEO", True),
                    show_edges=shared_controls.get("SHOW_EDGES", True),
                    show_roi=shared_controls.get("SHOW_ROI", True)
                )
                cv.imshow("Lane Detection", main_display)

            if cv.waitKey(1) == ord('q'):
                break
            mapped_direction = map_direction(direction)
            lane_data = {"speed": speed, "direction": mapped_direction}

            if not lane_queue.full():
                lane_queue.put(lane_data)

            frame_count, fps, avg_time, total_processing_time  = update_processing_time(shared_controls, start_time,
                                                                             total_processing_time,
                                                                             frame_count)
            shared_controls["car_info"] = lane_data
            shared_controls["time_info"] = {
                "fps": round(fps, 0),
                "total_processing_time": round(avg_time, 2)
            }

            cv2.imshow("warped", warped_roi)

    except Exception as e:
        print(f"{YELLOW}[LaneDetection]{RED}[ERROR] Lane Detection Error:{e}{RESET}")

    finally:
        video_proc.release()
        cv.destroyAllWindows()
