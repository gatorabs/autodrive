# object_detection.py
import cv2
import threading
from ultralytics import YOLO

TARGET_CLASSES = {0, 9}

class ObjectDetector(threading.Thread):
    def __init__(self, serial_data, controls, camera_source=0):
        super(ObjectDetector, self).__init__()
        self.serial_data = serial_data
        self.cap = cv2.VideoCapture(camera_source)
        self.model = YOLO('yolov8n.pt')
        self.running = True
        self.controls = controls
        self.lock = threading.Lock()
        self.window_open = False

    def run(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue

            frame = cv2.resize(frame, (320, 240))
            results = self.model(frame, classes=list(TARGET_CLASSES))
            person_detected = False

            for result in results:
                for box in result.boxes:
                    cls = int(box.cls[0])
                    if cls in TARGET_CLASSES:
                        if cls == 0:
                            person_detected = True
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        label = self.model.names[cls]
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, label, (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            with self.lock:
                self.serial_data[2] = 1 if person_detected else 0


            if self.controls["SHOW_PERSON_DETECTION"]:
                # Se o controle está ativo e a janela ainda não foi criada, crie-a
                if not self.window_open:
                    cv2.namedWindow("Object Detection")
                    self.window_open = True
                cv2.imshow("Object Detection", frame)
            else:
                # Se o controle estiver desativado e a janela estiver aberta, feche-a
                if self.window_open:
                    cv2.destroyWindow("Object Detection")
                    self.window_open = False


            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()

    def stop(self):
        self.running = False
