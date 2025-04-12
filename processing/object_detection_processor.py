import cv2
from ultralytics import YOLO
import torch

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

        # Inicializa valores padrão
        self.shared_serial_data[1] = 0  # semáforo
        self.shared_serial_data[2] = 0  # pessoa

        self.window_created = False
    def process_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        frame = cv2.resize(frame, (320, 240))
        results = self.model(frame, classes=list(TARGET_CLASSES), verbose=False)

        person_detected = False
        traffic_light_state = 0  # padrão: verde

        show_window = self.controls.get("SHOW_PERSON_DETECTION", True)

        target_box_height = self.controls.get("TARGET_BOX_HEIGHT", 250)
        tolerance = self.controls.get("TOLERANCE", 30)
        min_box_height = target_box_height - tolerance
        max_box_height = target_box_height

        for result in results:
            for box in result.boxes:
                cls = int(box.cls[0])
                if cls == 0:
                    # Pessoa
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    person_detected = True
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, "Person", (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                elif cls == 9:
                    # Semáforo
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                    cv2.putText(frame, f"TL: {traffic_light_state}", (x1, y1 - 20),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

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
