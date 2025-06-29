import cv2
from ultralytics import YOLO
import torch
import numpy as np
from extensions.constants.videoConstants import FRAME_HEIGHT, FRAME_WIDTH

TARGET_CLASSES = {0, 9}


class ObjectDetector:
    def __init__(self, shared_serial_data, shared_frames, tk_controls, camera_source=0, logger=None):
        self.shared_serial_data = shared_serial_data
        self.shared_frames = shared_frames
        self.tk_controls = tk_controls
        self.camera_source = camera_source
        self.logger = logger
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Usando dispositivo {self.device}")

        self.model = YOLO('yolov8n.pt')
        try:
            self.model.to(self.device)
        except Exception as e:
            logger.error(f"Não foi possível mover o modelo para o dispositivo desejado: {e}")

        # Detecta se é vídeo (caminho) ou câmera (índice ou string numérica)
        if isinstance(camera_source, str) and camera_source.isdigit():
            self.is_video = False
            self.cap = cv2.VideoCapture(int(camera_source), cv2.CAP_DSHOW)
        elif isinstance(camera_source, int):
            self.is_video = False
            self.cap = cv2.VideoCapture(camera_source, cv2.CAP_DSHOW)
        else:
            self.is_video = True
            self.cap = cv2.VideoCapture(camera_source)

        if not self.cap.isOpened():
            logger.error(f"Falha ao abrir o vídeo ou câmera ({camera_source}).")
            exit()

        # Inicializa valores padrão
        # 0: vermelho; 1: amarelo; 2: verde
        self.shared_serial_data[1] = 0  # semáforo
        self.shared_serial_data[2] = 0  # pessoa
        self.window_created = False

    def process_traffic_light_roi(self, roi):
        active_color = "Unknown"
        color_bgr = (255, 255, 255)  # branco padrão
        traffic_light_state = 2  # padrão: verde

        if roi.size != 0:
            # 1) converte para gray e dá um leve blur para reduzir ruído
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (5, 5), 0)

            # 2) dimensões
            h = gray.shape[0]
            h_third = h // 3

            # 3) extrai as 3 regiões
            red_roi = gray[0:h_third, :]
            yellow_roi = gray[h_third:2 * h_third, :]
            green_roi = gray[2 * h_third:h, :]

            # 4) calcula a média de intensidade em cada região
            mean_red = np.mean(red_roi)
            mean_yellow = np.mean(yellow_roi)
            mean_green = np.mean(green_roi)

            means = {
                "Red": mean_red,
                "Yellow": mean_yellow,
                "Green": mean_green
            }

            active_color = max(means, key=means.get)

            # 6) mapeia o resultado para BGR e estado
            if active_color == "Red":
                color_bgr = (0, 0, 255)
                traffic_light_state = 0
            elif active_color == "Yellow":
                color_bgr = (0, 255, 255)
                traffic_light_state = 1
            elif active_color == "Green":
                color_bgr = (0, 255, 0)
                traffic_light_state = 2

        return active_color, color_bgr, traffic_light_state

    def process_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            # Se o vídeo chegar ao fim, volta ao início
            if self.is_video:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
                if not ret:
                    return
            else:
                return

        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
        results = self.model(frame, classes=list(TARGET_CLASSES), verbose=False)

        person_detected = False
        # Estado default para o semáforo
        traffic_light_state = 2

        min_person_height = self.tk_controls["Person"]
        min_traffic_height = self.tk_controls["Traffic"]

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

        _, jpeg_frame = cv2.imencode('.jpg', frame)
        self.shared_frames["object"] = jpeg_frame.tobytes()

    def cleanup(self):
        self.cap.release()
        cv2.destroyAllWindows()
