import multiprocessing as mp
import cv2 as cv
import time

from controllers.pid_controller import PIDController
from controllers.lane_detector import LaneDetector
from controllers.serial_comm import SerialCommunicator
from processing.video_processor import VideoProcessor
from processing.priorities_processor import set_process_priority
from processing.warp_perspective_processor import bird_eye
from processing.object_detection_processor import ObjectDetector
from utils.display import draw_overlays, create_main_window
from utils.real_time_trackbars import create_control_window, get_trackbar_values
from utils.buttons import create_tkinter_controls

def lane_detection_process(lane_queue, shared_controls):
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

    VIDEO_SOURCE = "test_videos/teste1.mp4"
    create_control_window()

    pid = PIDController(TARGET_CENTER_DISTANCE, KP, KI, KD, MIN_OUTPUT, MAX_OUTPUT)
    lane_detector = LaneDetector(ROI_START, ROI_END)
    video_proc = VideoProcessor(VIDEO_SOURCE, FRAME_WIDTH, FRAME_HEIGHT)
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


def object_detection_process(object_queue, shared_controls):
    set_process_priority("high")
    object_serial_data = shared_controls["object_serial_data"]
    object_detector = ObjectDetector(object_serial_data, shared_controls)
    object_detector.start()

    try:
        send_interval = 0.05  # intervalo em segundos
        last_put_time = time.time()
        while True:
            current_time = time.time()
            if (current_time - last_put_time) >= send_interval:
                object_data = {"person": object_serial_data[2], "semaforo": 0}  # 'semaforo' mockado
                if not object_queue.full():
                    object_queue.put(object_data)
                last_put_time = time.time()
            else:
                remaining = send_interval - (current_time - last_put_time)
                timer_event = mp.Event()
                timer_event.wait(remaining)
                timer_event.clear()
    except Exception as e:
        print("Object Detection Error:", e)
    finally:
        object_detector.stop()
        cv.destroyAllWindows()


def data_sender_process(lane_queue, object_queue, shared_controls):
    set_process_priority("above_normal")
    SEND_DATA = True
    COM_PORT = 'COM5'
    serial_comm = SerialCommunicator(COM_PORT, send_data=SEND_DATA)

    lane_data = {"speed": 255, "direction": 180}
    obj_data = {"person": 0, "semaforo": 0}
    send_interval = 0.01  # intervalo de envio em segundos
    last_send_time = time.time()

    try:
        while True:
            if not lane_queue.empty():
                lane_data = lane_queue.get()
            if not object_queue.empty():
                obj_data = object_queue.get()

            if obj_data.get("person", 0) == 1 or shared_controls.get("EMERGENCY_STOP", 0) == 1:
                lane_data["speed"] = 0

            current_time = time.time()
            if (current_time - last_send_time) >= send_interval:
                data_to_send = [
                    lane_data.get("direction", 180),
                    lane_data.get("speed", 255),
                    obj_data.get("semaforo", 0)
                ]
                serial_comm.send(data_to_send)
                last_send_time = time.time()
            else:
                sleep_time = max(0, send_interval - (current_time - last_send_time))
                time.sleep(sleep_time)
    except Exception as e:
        print("Data Sender Error:", e)
    finally:
        serial_comm.close()


def security_process(shared_controls):
    set_process_priority("high")
    OPEN_FOR_RECEIVE = True
    SECURITY_COM_PORT = 'COM3'
    BAUD_RATE = 115200
    sec_serial = SerialCommunicator(SECURITY_COM_PORT, baud_rate=BAUD_RATE, open_for_receive=OPEN_FOR_RECEIVE)
    try:
        while True:
            data = sec_serial.receive()
            if data is not None:
                # Se receber 's' ou 'S', ativa a flag; caso contrário, desativa
                if b's' in data or b'S' in data:
                    shared_controls["EMERGENCY_STOP"] = 1
                    print("Emergency Stop triggered!")
                else:
                    shared_controls["EMERGENCY_STOP"] = 0
            else:
                shared_controls["EMERGENCY_STOP"] = 0
            time.sleep(0.01)
    except Exception as e:
        print("Security Process Error:", e)
    finally:
        sec_serial.close()


if __name__ == '__main__':
    mp.set_start_method('spawn')
    manager = mp.Manager()

    shared_controls = manager.dict({
       "SHOW_VIDEO": True,
       "SHOW_EDGES": True,
       "SHOW_ROI": True,
       "SHOW_PERSON_DETECTION": True,
       "SHOW_FPS": True,
       "EMERGENCY_STOP": 0,
       "object_serial_data": manager.list([0, 0, 0])
    })

    lane_queue = mp.Queue(maxsize=10)
    object_queue = mp.Queue(maxsize=10)

    lane_process = mp.Process(target=lane_detection_process, args=(lane_queue, shared_controls))
    object_process = mp.Process(target=object_detection_process, args=(object_queue, shared_controls))
    sender_process = mp.Process(target=data_sender_process, args=(lane_queue, object_queue, shared_controls))
    tk_process = mp.Process(target=create_tkinter_controls, args=(shared_controls,))
    security_proc = mp.Process(target=security_process, args=(shared_controls,))

    lane_process.start()
    object_process.start()
    sender_process.start()
    tk_process.start()
    security_proc.start()

    try:
        lane_process.join()
        object_process.join()
        sender_process.join()
        tk_process.join()
        security_proc.join()
    except KeyboardInterrupt:
        print("Interrompido pelo usuário. Encerrando processos...")
        lane_process.terminate()
        object_process.terminate()
        sender_process.terminate()
        tk_process.terminate()
        security_proc.terminate()
