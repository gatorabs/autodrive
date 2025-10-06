import os
from typing import Iterable, List, Optional, Sequence, Set, Union

import cv2
from ultralytics import YOLO
import torch
from src.infrastructure.services.object_detection_service import process_traffic_light_roi
from src.infrastructure.adapters.video.video_process import VideoProcessor
from src.infrastructure.constants.video_constants import (
    FRAME_WIDTH,
    FRAME_HEIGHT,
    CPU_INFERENCE_IMG_SIZE,
)

TARGET_CLASSES = {0, 9}
MODEL_CONTROL_KEY = "OBJECT_MODEL_PATH"
CUSTOM_MODEL_CONTROL_KEY = "CUSTOM_OBJECT_MODEL_PATH"
CUSTOM_CLASSES_CONTROL_KEY = "CUSTOM_OBJECT_CLASSES"
CUSTOM_CONFIDENCE_CONTROL_KEY = "CUSTOM_OBJECT_CONFIDENCE"
DEFAULT_MODEL_PATH = "yolov8n.pt"
DEFAULT_CUSTOM_CONFIDENCE = 0.35
CUSTOM_DETECTION_COLOR = (255, 0, 0)

class ObjectDetector:
    def __init__(self,
                 shared_serial_data,
                 shared_frames,
                 tk_controls,
                 camera_source=0,
                 logger=None,
                 video_processor=None,
                 model_path=None,
                 custom_model_path=None,
                 custom_model_classes: Optional[Union[str, Sequence[Union[str, int]]]] = None,
                 custom_model_confidence: Optional[Union[str, float]] = None):

        self.shared_serial_data = shared_serial_data
        self.shared_frames = shared_frames
        self.tk_controls = tk_controls
        self.logger = logger

        self.video_processor = video_processor
        if self.video_processor is None and camera_source is not None:
            self.video_processor = VideoProcessor(
                video_source=camera_source,
                frame_width=FRAME_WIDTH,
                frame_height=FRAME_HEIGHT,
            )

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        if self.logger:
            self.logger.info(f"Usando dispositivo {self.device}")

        configured_model_path = self._get_control_value(MODEL_CONTROL_KEY)
        env_model_path = os.getenv("YOLO_MODEL_PATH")

        self.model_path = model_path or configured_model_path or env_model_path or DEFAULT_MODEL_PATH

        if self.logger:
            self.logger.info(f"Carregando modelo YOLO base de '{self.model_path}'")

        try:
            self.model = YOLO(self.model_path)
            self.model.to(self.device)
            self.model.eval()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Falha ao carregar modelo YOLO base: {e}")
            raise

        self.custom_detections = []

        self.custom_model_path = custom_model_path or self._get_control_value(CUSTOM_MODEL_CONTROL_KEY)
        if not self.custom_model_path:
            self.custom_model_path = os.getenv("YOLO_CUSTOM_MODEL_PATH")
        if isinstance(self.custom_model_path, str) and not self.custom_model_path.strip():
            self.custom_model_path = None

        self.custom_model_confidence = self._parse_confidence(custom_model_confidence)
        if self.custom_model_confidence is None:
            self.custom_model_confidence = self._parse_confidence(self._get_control_value(CUSTOM_CONFIDENCE_CONTROL_KEY))
        if self.custom_model_confidence is None:
            self.custom_model_confidence = self._parse_confidence(os.getenv("YOLO_CUSTOM_CONFIDENCE"))
        if self.custom_model_confidence is None:
            self.custom_model_confidence = DEFAULT_CUSTOM_CONFIDENCE

        self.custom_model_classes = self._parse_custom_classes(custom_model_classes)
        if not self.custom_model_classes:
            self.custom_model_classes = self._parse_custom_classes(self._get_control_value(CUSTOM_CLASSES_CONTROL_KEY))
        if not self.custom_model_classes:
            self.custom_model_classes = self._parse_custom_classes(os.getenv("YOLO_CUSTOM_CLASSES"))

        self.custom_model = None
        self.uses_shared_model = False
        self.custom_class_ids: Optional[Set[int]] = None
        if self.custom_model_path:
            try:
                if os.path.abspath(self.custom_model_path) == os.path.abspath(self.model_path):
                    self.custom_model = self.model
                    self.uses_shared_model = True
                    if self.logger:
                        self.logger.info("Usando o mesmo modelo YOLO para detecção base e personalizada")
                else:
                    if self.logger:
                        self.logger.info(f"Carregando modelo YOLO personalizado de '{self.custom_model_path}'")
                    self.custom_model = YOLO(self.custom_model_path)
                    self.custom_model.to(self.device)
                    self.custom_model.eval()
                self.custom_class_ids = self._resolve_custom_class_ids(self.custom_model_classes)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Falha ao carregar modelo YOLO personalizado: {e}")
                self.custom_model = None
                self.custom_class_ids = None

        self.inference_kwargs = {
            "verbose": False,
        }
        if not self.uses_shared_model:
            self.inference_kwargs["classes"] = list(TARGET_CLASSES)

        if self.device == "cuda":
            self.inference_kwargs["half"] = True  # FP16 na GPU
        else:
            self.inference_kwargs["imgsz"] = CPU_INFERENCE_IMG_SIZE

        self.custom_inference_kwargs = {
            "verbose": False,
        }
        if self.custom_model_confidence is not None:
            self.custom_inference_kwargs["conf"] = self.custom_model_confidence
        if self.device == "cuda":
            self.custom_inference_kwargs["half"] = True
        else:
            self.custom_inference_kwargs["imgsz"] = CPU_INFERENCE_IMG_SIZE

        self.shared_serial_data[1] = 0  # semáforo
        self.shared_serial_data[2] = 0  # pessoa

    def process_frame(self, frame):
        try:
            base_inference_kwargs = dict(self.inference_kwargs)
            if self.uses_shared_model and "classes" in base_inference_kwargs:
                base_inference_kwargs.pop("classes", None)

            with torch.inference_mode():
                results = self.model(frame, **base_inference_kwargs)

            person_detected = False
            traffic_light_state = 2

            min_person_size = self.tk_controls["Person"]
            min_traffic_size = self.tk_controls["Traffic"]

            for result in results:
                for box in result.boxes:
                    cls = int(box.cls[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    box_height = y2 - y1
                    box_width = x2 - x1

                    if cls == 0 and (box_height >= min_person_size or box_width >= min_person_size):
                        person_detected = True
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, "Person", (x1, max(y1 - 10, 0)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                    elif cls == 9 and (box_height >= min_traffic_size or box_width >= min_traffic_size):
                        roi = frame[y1:y2, x1:x2]
                        active_color, color_bgr, traffic_light_state = process_traffic_light_roi(roi)

                        y_div1 = y1 + box_height // 3
                        y_div2 = y1 + 2 * (box_height // 3)

                        cv2.line(frame, (x1, y_div1), (x2, y_div1), (255, 255, 255), 1)
                        cv2.line(frame, (x1, y_div2), (x2, y_div2), (255, 255, 255), 1)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color_bgr, 2)
                        cv2.putText(frame, f"TL: {active_color}", (x1, max(y1 - 20, 0)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_bgr, 2)

            self.custom_detections = []
            if self.custom_model:
                try:
                    if self.uses_shared_model:
                        self.custom_detections = self._extract_custom_detections(frame, results)
                    else:
                        with torch.inference_mode():
                            custom_results = self.custom_model(frame, **self.custom_inference_kwargs)
                        self.custom_detections = self._extract_custom_detections(frame, custom_results)
                except Exception as custom_error:
                    if self.logger:
                        self.logger.error(f"Falha ao executar detecção personalizada: {custom_error}")
                    self.custom_detections = []

            return person_detected, traffic_light_state

        except Exception as e:
            if self.logger:
                self.logger.error(f"Erro ao processar frame: {e}")

    def cleanup(self):
        if self.video_processor:
            self.video_processor.release()
        cv2.destroyAllWindows()

    def _extract_custom_detections(self, frame, results) -> List[dict]:
        detections: List[dict] = []
        if not results:
            return detections

        for result in results:
            if not hasattr(result, "boxes"):
                continue
            for box in result.boxes:
                cls_idx = int(box.cls[0])
                if self.custom_class_ids is not None and cls_idx not in self.custom_class_ids:
                    continue
                if self.custom_class_ids is None and cls_idx in TARGET_CLASSES:
                    continue

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = float(box.conf[0]) if hasattr(box, "conf") else 0.0
                if self.custom_model_confidence is not None and confidence < self.custom_model_confidence:
                    continue
                label = self._resolve_custom_label(cls_idx)

                detections.append({
                    "class_id": cls_idx,
                    "label": label,
                    "confidence": confidence,
                    "bbox": [x1, y1, x2, y2],
                })

                cv2.rectangle(frame, (x1, y1), (x2, y2), CUSTOM_DETECTION_COLOR, 2)
                cv2.putText(frame,
                            f"{label} {confidence:.2f}",
                            (x1, max(y1 - 10, 0)),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            CUSTOM_DETECTION_COLOR,
                            2)

        return detections

    def _resolve_custom_label(self, class_id: int) -> str:
        if not self.custom_model or not hasattr(self.custom_model, "names"):
            return str(class_id)
        names = self.custom_model.names
        if isinstance(names, dict):
            return names.get(class_id, str(class_id))
        if isinstance(names, (list, tuple)) and 0 <= class_id < len(names):
            return names[class_id]
        return str(class_id)

    def _get_control_value(self, key: str):
        if not self.tk_controls:
            return None
        try:
            return self.tk_controls.get(key)
        except Exception:
            return None

    def _parse_confidence(self, value: Optional[Union[str, float]]) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(max(0.0, min(1.0, value)))
        try:
            parsed = float(str(value).strip())
            return float(max(0.0, min(1.0, parsed)))
        except (ValueError, TypeError):
            return None

    def _parse_custom_classes(self, classes: Optional[Union[str, Sequence[Union[str, int]]]]) -> Set[Union[str, int]]:
        parsed: Set[Union[str, int]] = set()
        if classes is None:
            return parsed

        values: Iterable
        if isinstance(classes, (list, tuple, set)):
            values = classes
        else:
            values = str(classes).split(",")

        for item in values:
            if item is None:
                continue
            if isinstance(item, str):
                stripped = item.strip()
                if not stripped:
                    continue
                if stripped.isdigit():
                    parsed.add(int(stripped))
                else:
                    parsed.add(stripped.lower())
            elif isinstance(item, (int, float)):
                parsed.add(int(item))

        return parsed

    def _resolve_custom_class_ids(self, classes: Set[Union[str, int]]) -> Optional[Set[int]]:
        if not classes:
            return None
        if not self.custom_model or not hasattr(self.custom_model, "names"):
            return None

        resolved: Set[int] = set()
        names = self.custom_model.names
        name_map = {}
        if isinstance(names, dict):
            name_map = {str(v).lower(): int(k) for k, v in names.items()}
        elif isinstance(names, (list, tuple)):
            name_map = {str(name).lower(): idx for idx, name in enumerate(names)}

        for item in classes:
            if isinstance(item, int):
                resolved.add(item)
            elif isinstance(item, str):
                lowered = item.lower()
                if lowered.isdigit():
                    resolved.add(int(lowered))
                elif lowered in name_map:
                    resolved.add(name_map[lowered])

        return resolved if resolved else None
