import cv2
from ultralytics import YOLO
import torch

from utils.real_time_trackbars import create_object_roi_control_window, get_object_roi_trackbar_values

TARGET_CLASSES = {0, 9}


class ObjectDetector:
    def __init__(self, shared_serial_data, controls, camera_source=0):
        self.shared_serial_data = shared_serial_data
        self.controls = controls
        self.camera_source = camera_source

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"ObjectDetector: Usando dispositivo {self.device}")

        self.model = YOLO('yolov8n.pt')
        try:
            self.model.to(self.device)
        except Exception as e:
            print("Não foi possível mover o modelo para o dispositivo desejado:", e)

        self.cap = cv2.VideoCapture(self.camera_source)
        if not self.cap.isOpened():
            print("Falha ao abrir o vídeo ou câmera.")
            exit()

        # Inicializa valores padrão
        # 0: vermelho; 1: amarelo; 2: verde
        self.shared_serial_data[1] = 0
        self.shared_serial_data[2] = 0  # pessoa

        self.window_created = False

        create_object_roi_control_window()

    def process_traffic_light_roi(self, roi):
        active_color = "Unknown"
        color_bgr = (255, 255, 255)  # padrão: branco
        traffic_light_state = 2  # valor default: verde

        if roi.size != 0:
            h, w, _ = roi.shape
            # Define as três regiões horizontais
            red_roi = roi[0: h // 3, :]
            yellow_roi = roi[h // 3: 2 * h // 3, :]
            green_roi = roi[2 * h // 3: h, :]

            # Cálculo simples das intensidades:
            red_mean = red_roi[:, :, 2].mean()  # canal vermelho
            green_mean = green_roi[:, :, 1].mean()  # canal verde
            yellow_mean = ((yellow_roi[:, :, 2] + yellow_roi[:, :, 1]) / 2).mean()  # média para amarelo

            # Determina a cor ativa com base na intensidade de cada região
            if red_mean > yellow_mean and red_mean > green_mean:
                active_color = "Red"
                color_bgr = (0, 0, 255)
                traffic_light_state = 0
            elif yellow_mean > red_mean and yellow_mean > green_mean:
                active_color = "Yellow"
                color_bgr = (0, 255, 255)
                traffic_light_state = 1
            else:
                active_color = "Green"
                color_bgr = (0, 255, 0)
                traffic_light_state = 2

        return active_color, color_bgr, traffic_light_state

    def process_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            # Se o vídeo chegar ao fim, volta ao início
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()
            if not ret:
                return

        frame = cv2.resize(frame, (320, 240))
        results = self.model(frame, classes=list(TARGET_CLASSES), verbose=False)

        person_detected = False
        # Estado default para o semáforo
        traffic_light_state = 2

        show_window = self.controls.get("SHOW_PERSON_DETECTION", True)
        min_person_height, min_traffic_height = get_object_roi_trackbar_values()

        for result in results:
            for box in result.boxes:
                cls = int(box.cls[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                box_height = y2 - y1

                if cls == 0 and box_height >= min_person_height:
                    person_detected = True
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, "Person", (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                elif cls == 9 and box_height >= min_traffic_height:
                    roi = frame[y1:y2, x1:x2]
                    active_color, color_bgr, traffic_light_state = self.process_traffic_light_roi(roi)

                    y_div1 = y1 + box_height // 3
                    y_div2 = y1 + 2 * (box_height // 3)

                    cv2.line(frame, (x1, y_div1), (x2, y_div1), (255, 255, 255), 1)
                    cv2.line(frame, (x1, y_div2), (x2, y_div2), (255, 255, 255), 1)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color_bgr, 2)
                    cv2.putText(frame, f"TL: {active_color}", (x1, y1 - 20),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_bgr, 2)

        self.shared_serial_data[2] = 1 if person_detected else 0
        self.shared_serial_data[1] = traffic_light_state

        if show_window:
            if not self.window_created:
                cv2.namedWindow("Object Detection", cv2.WINDOW_NORMAL)
                self.window_created = True
            cv2.imshow("Object Detection", frame)
            cv2.waitKey(1)
        else:
            if self.window_created:
                try:
                    cv2.destroyWindow("Object Detection")
                except cv2.error as e:
                    print("Erro ao destruir janela:", e)
                self.window_created = False

    def cleanup(self):
        self.cap.release()
        cv2.destroyAllWindows()
