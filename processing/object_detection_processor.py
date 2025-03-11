import cv2
from ultralytics import YOLO
import multiprocessing as mp

TARGET_CLASSES = {0, 9}

class ObjectDetector(mp.Process):
    def __init__(self, shared_serial_data, controls, camera_source=0):
        super(ObjectDetector, self).__init__()
        self.shared_serial_data = shared_serial_data  # Este é o manager.list compartilhado
        self.controls = controls
        self.camera_source = camera_source
        self.model = YOLO('yolov8n.pt')
        self.running = mp.Value('b', True)

    def run(self):
        cap = cv2.VideoCapture(self.camera_source)
        while self.running.value:
            ret, frame = cap.read()
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

            # Atualiza o valor compartilhado: índice 2 para detecção de pessoa
            self.shared_serial_data[2] = 1 if person_detected else 0

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
