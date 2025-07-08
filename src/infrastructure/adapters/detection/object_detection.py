import cv2
from ultralytics import YOLO
import torch
from src.infrastructure.constants.video_constants import FRAME_HEIGHT, FRAME_WIDTH
from src.application.services.object_detection_service import process_traffic_light_roi, publish_results
from src.infrastructure.adapters.video.video_process import VideoProcessor

TARGET_CLASSES = {0, 9}

class ObjectDetector:
    def __init__(self,
                 shared_serial_data,
                 shared_frames,
                 tk_controls,
                 camera_source=0,
                 logger=None):

        self.shared_serial_data = shared_serial_data
        self.shared_frames = shared_frames
        self.tk_controls = tk_controls
        self.logger = logger

        self.video_processor = VideoProcessor(
            camera_source,
            frame_width=FRAME_WIDTH,
            frame_height=FRAME_HEIGHT
        )

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Usando dispositivo {self.device}")

        self.model = YOLO('yolov8n.pt')
        try:
            self.model.to(self.device)
        except Exception as e:
            logger.error(f"Não foi possível mover o modelo para o dispositivo desejado: {e}")

        self.shared_serial_data[1] = 0  # semáforo
        self.shared_serial_data[2] = 0  # pessoa

    def process_frame(self):
        try:
            frame = self.video_processor.get_frame()
        except Exception as e:
            self.logger.error(f"Erro ao capturar frame: {e}")
            return

        results = self.model(frame, classes=list(TARGET_CLASSES), verbose=False)

        person_detected = False
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
                    active_color, color_bgr, traffic_light_state = process_traffic_light_roi(roi)

                    y_div1 = y1 + box_height // 3
                    y_div2 = y1 + 2 * (box_height // 3)

                    cv2.line(frame, (x1, y_div1), (x2, y_div1), (255, 255, 255), 1)
                    cv2.line(frame, (x1, y_div2), (x2, y_div2), (255, 255, 255), 1)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color_bgr, 2)
                    cv2.putText(frame, f"TL: {active_color}", (x1, y1 - 20),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_bgr, 2)

        publish_results(
            shared_serial_data=self.shared_serial_data,
            shared_frames=self.shared_frames,
            person_detected=person_detected,
            traffic_light_state=traffic_light_state,
            frame=frame
        )

    def cleanup(self):
        self.video_processor.release()
        cv2.destroyAllWindows()
