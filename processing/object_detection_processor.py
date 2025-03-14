import cv2
from ultralytics import YOLO
import multiprocessing as mp
import torch

TARGET_CLASSES = {0, 9}

class ObjectDetector(mp.Process):
    def __init__(self, shared_serial_data, controls, camera_source=0):
        super(ObjectDetector, self).__init__()
        self.shared_serial_data = shared_serial_data
        self.controls = controls
        self.camera_source = camera_source

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"ObjectDetector: Usando dispositivo {self.device}")

        self.model = YOLO('yolov8n.pt')
        try:
            self.model.model.to(self.device)
        except Exception as e:
            print("Não foi possível mover o modelo para o dispositivo desejado:", e)

        self.running = mp.Value('b', True)

    def run(self):
        cap = cv2.VideoCapture(self.camera_source)
        # Inicializa o estado do semáforo como verde (0) e pessoa como 0
        self.shared_serial_data[1] = 0  # semáforo: 0=verde, 1=amarelo, 2=vermelho
        self.shared_serial_data[2] = 0  # pessoa: 1 detectada, 0 não detectada

        while self.running.value:
            ret, frame = cap.read()
            if not ret:
                continue

            frame = cv2.resize(frame, (320, 240))
            results = self.model(frame, classes=list(TARGET_CLASSES))
            person_detected = False
            traffic_light_state = 0  # padrão: verde

            # Parâmetros para filtro (trackbar)
            target_box_height = self.controls.get("TARGET_BOX_HEIGHT", 250)
            tolerance = self.controls.get("TOLERANCE", 30)
            min_box_height = target_box_height - tolerance
            max_box_height = target_box_height

            for result in results:
                for box in result.boxes:
                    cls = int(box.cls[0])
                    if cls in TARGET_CLASSES:
                        if cls == 0:
                            # Detecção de pessoa
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            # box_height = y2 - y1
                            # if box_height < min_box_height or box_height > max_box_height:
                            #     continue
                            person_detected = True
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            cv2.putText(frame, "Person", (x1, y1 - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                        elif cls == 9:
                            # Detecção de semáforo
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                            cv2.putText(frame, f"TL: {traffic_light_state}", (x1, y1 - 20),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            self.shared_serial_data[2] = 1 if person_detected else 0
            self.shared_serial_data[1] = traffic_light_state

            if self.controls.get("SHOW_PERSON_DETECTION", True):
                cv2.namedWindow("Object Detection", cv2.WINDOW_NORMAL)
                cv2.imshow("Object Detection", frame)
            else:
                cv2.destroyWindow("Object Detection")

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

    def stop(self):
        self.running.value = False
