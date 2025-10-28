from collections import defaultdict
from pathlib import Path

import cv2
from ultralytics import YOLO
import torch
from src.infrastructure.services.object_detection_service import (
    process_traffic_light_roi,
)
from src.infrastructure.adapters.video.video_process import VideoProcessor
from src.infrastructure.constants.video_constants import (
    FRAME_WIDTH,
    FRAME_HEIGHT,
    CPU_INFERENCE_IMG_SIZE,
)

from .custom_model_utils import load_names_from_metadata, normalise_names_payload

TARGET_CLASSES = {0, 9}
DEFAULT_CUSTOM_MODEL_PATH = Path("runs/detect/train/weights/best.pt")
DEFAULT_CUSTOM_LABEL = "Custom Object"
DEFAULT_CUSTOM_CONFIDENCE = 0.35
DEFAULT_BASE_CONFIDENCE = 0.35
BASE_CONF_KEY = "BaseConf"
CUSTOM_CONF_KEY = "CustomConf"
CUSTOM_BOX_COLOR = (255, 140, 0)
PERSON_REGION_WIDTH_KEY = "PeopleRegion"
DEFAULT_PERSON_REGION_PERCENT = 33
CUSTOM_NMS_IOU_THRESHOLD = 0.45

CUSTOM_CLASS_SLIDER_KEYS = {
    "PLACA_PARE": "PLACA_PARE",
    "PLACA_DESVIO": "PLACA_DESVIO",
    "PLACA_LOMBADA": "PLACA_LOMBADA",
    "SEMAFORO": "SEMAFORO",
}

class ObjectDetector:
    def __init__(self,
                 shared_serial_data,
                 shared_frames,
                 tk_controls,
                 camera_source=0,
                 logger=None,
                 video_processor=None):

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
        logger.info(f"Usando dispositivo {self.device}")

        try:
            self.model = YOLO('yolov8n.pt')
            self.model.to(self.device)
            self.model.eval()
        except Exception as e:
            logger.error(f"Falha ao carregar modelo YOLO: {e}")
            raise

        self.inference_kwargs = {
            "classes": list(TARGET_CLASSES),
            "verbose": False,
        }

        if self.device == "cuda":
            self.inference_kwargs["half"] = True  # FP16 na GPU
        else:
            self.inference_kwargs["imgsz"] = CPU_INFERENCE_IMG_SIZE

        self.custom_models = []
        self.custom_default_label = DEFAULT_CUSTOM_LABEL
        self.custom_default_conf = DEFAULT_CUSTOM_CONFIDENCE
        self.base_default_conf = DEFAULT_BASE_CONFIDENCE
        self.custom_inference_kwargs = {
            "verbose": False,
        }

        if self.device == "cuda":
            self.custom_inference_kwargs["half"] = True
        else:
            self.custom_inference_kwargs["imgsz"] = CPU_INFERENCE_IMG_SIZE

        self._load_custom_models()

        self.shared_serial_data[1] = 0  # semáforo
        self.shared_serial_data[2] = 0  # pessoa
        if len(self.shared_serial_data) > 0:
            self.shared_serial_data[0] = 0  # objeto customizado

        if PERSON_REGION_WIDTH_KEY not in self.tk_controls:
            self.tk_controls[PERSON_REGION_WIDTH_KEY] = DEFAULT_PERSON_REGION_PERCENT
        if BASE_CONF_KEY not in self.tk_controls:
            self.tk_controls[BASE_CONF_KEY] = int(round(self.base_default_conf * 10))
        if CUSTOM_CONF_KEY not in self.tk_controls:
            self.tk_controls[CUSTOM_CONF_KEY] = int(round(self.custom_default_conf * 10))

    def _get_base_confidence(self):
        slider_value = self.tk_controls.get(BASE_CONF_KEY)
        if slider_value is None:
            return self.base_default_conf
        try:
            return max(0.05, min(0.99, float(slider_value) / 10.0))
        except (TypeError, ValueError):
            return self.base_default_conf

    def _candidate_search_roots(self):
        roots = [Path.cwd()]

        try:
            repo_root = Path(__file__).resolve().parents[4]
        except IndexError:
            repo_root = None

        if repo_root and repo_root not in roots:
            roots.append(repo_root)

        utils_dir = repo_root / "utils" if repo_root else None
        if utils_dir and utils_dir.exists():
            roots.append(utils_dir)
            model_trainer_dir = utils_dir / "model_trainer"
            if model_trainer_dir.exists():
                roots.append(model_trainer_dir)

        # Preserve order but remove duplicates
        seen = set()
        ordered_roots = []
        for root in roots:
            if root not in seen:
                ordered_roots.append(root)
                seen.add(root)
        return ordered_roots

    def _discover_custom_model_paths(self):
        search_roots = self._candidate_search_roots()
        def add_path(path_obj, bucket, seen):
            try:
                resolved = path_obj.resolve()
            except Exception:
                resolved = path_obj

            if not path_obj.exists() or resolved in seen:
                return

            seen.add(resolved)
            bucket.append(path_obj)

        seen_paths = set()
        discovered = []

        for root in search_roots:
            default_candidate = (root / DEFAULT_CUSTOM_MODEL_PATH)
            if default_candidate.exists():
                add_path(default_candidate, discovered, seen_paths)

        for root in search_roots:
            runs_dir = root / "runs" / "detect"
            if not runs_dir.exists():
                continue
            for weight_path in runs_dir.glob("*/weights/best.pt"):
                add_path(weight_path, discovered, seen_paths)

        try:
            discovered.sort(key=lambda path: path.stat().st_mtime, reverse=True)
        except OSError:
            pass

        return discovered

    def _load_custom_models(self):
        self.custom_models = []
        model_paths = self._discover_custom_model_paths()
        if not model_paths:
            if self.logger:
                self.logger.info(
                    "Nenhum modelo customizado encontrado. Detecção extra desativada.")
            return

        covered_classes = set()

        for model_path in model_paths:
            try:
                model = YOLO(str(model_path))
                model.to(self.device)
                model.eval()

                names_payload = normalise_names_payload(getattr(model, "names", {}))
                if not names_payload:
                    names_payload = load_names_from_metadata(model_path)

                if isinstance(names_payload, dict):
                    names_iterable = names_payload.values()
                else:
                    names_iterable = names_payload or []

                class_names = {
                    str(name).strip()
                    for name in names_iterable
                    if str(name).strip()
                }
                if class_names and class_names.issubset(covered_classes):
                    if self.logger:
                        classes_repr = ", ".join(sorted(class_names))
                        self.logger.info(
                            f"Ignorando modelo customizado {model_path} (classes já cobertas: {classes_repr})"
                        )
                    continue

                self.custom_models.append({
                    "model": model,
                    "names": names_payload,
                    "path": model_path,
                })
                if self.logger:
                    if names_payload:
                        classes = ", ".join(sorted(names_payload.values()))
                        self.logger.info(
                            f"Modelo customizado carregado de {model_path} (classes: {classes})"
                        )
                    else:
                        self.logger.info(
                            f"Modelo customizado carregado de {model_path} (nomes não informados)"
                        )
                covered_classes.update(class_names)
            except Exception as exc:
                if self.logger:
                    self.logger.error(f"Falha ao carregar modelo customizado ({model_path}): {exc}")

    def _get_custom_label(self, cls_id, names):
        if isinstance(names, dict):
            try:
                return names[int(cls_id)]
            except (KeyError, TypeError, ValueError):
                pass
        return self.custom_default_label

    def _get_custom_confidence(self):
        slider_value = self.tk_controls.get(CUSTOM_CONF_KEY)
        if slider_value is None:
            return self.custom_default_conf
        try:
            return max(0.05, min(0.99, float(slider_value) / 10.0))
        except (TypeError, ValueError):
            return self.custom_default_conf

    def _get_custom_size_thresholds(self):
        thresholds = {}
        for label, slider_key in CUSTOM_CLASS_SLIDER_KEYS.items():
            slider_value = self.tk_controls.get(slider_key)
            try:
                thresholds[label] = max(0.0, float(slider_value))
            except (TypeError, ValueError):
                thresholds[label] = 0.0
        return thresholds

    def process_frame(self, frame):
        try:
            with torch.inference_mode():
                base_conf = self._get_base_confidence()
                results = self.model(
                    frame,
                    conf=base_conf,
                    **self.inference_kwargs,
                )
                custom_results = []
                custom_conf = None
                if self.custom_models:
                    custom_conf = self._get_custom_confidence()
                    for custom_model in self.custom_models:
                        model = custom_model["model"]
                        model_results = model(
                            frame,
                            conf=custom_conf,
                            **self.custom_inference_kwargs,
                        )
                        custom_results.append((custom_model, model_results))

            person_detected = False
            traffic_light_state = 2
            detected_custom_labels = set()

            min_person_size = self.tk_controls["Person"]
            custom_size_thresholds = self._get_custom_size_thresholds()

            frame_height, frame_width = frame.shape[:2]
            person_region_percent = self.tk_controls.get(
                PERSON_REGION_WIDTH_KEY,
                DEFAULT_PERSON_REGION_PERCENT,
            )
            try:
                person_region_percent = float(person_region_percent)
            except (TypeError, ValueError):
                person_region_percent = DEFAULT_PERSON_REGION_PERCENT

            person_region_percent = max(1.0, min(100.0, person_region_percent))
            region_width = max(1.0, frame_width * (person_region_percent / 100.0))
            half_region_width = max(1, int(round(region_width / 2)))
            frame_center_x = frame_width // 2
            left_person_boundary = max(0, frame_center_x - half_region_width)
            right_person_boundary = min(frame_width - 1, frame_center_x + half_region_width)

            overlay = frame.copy()
            cv2.rectangle(
                overlay,
                (left_person_boundary, 0),
                (right_person_boundary, frame_height - 1),
                (255, 0, 0),
                -1,
            )
            cv2.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)

            line_color = (255, 0, 0)
            cv2.line(frame, (left_person_boundary, 0), (left_person_boundary, frame_height), line_color, 2)
            cv2.line(frame, (right_person_boundary, 0), (right_person_boundary, frame_height), line_color, 2)

            for result in results:
                for box in result.boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0]) if hasattr(box, "conf") else 0.0
                    if conf < base_conf:
                        continue
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    box_height = y2 - y1
                    box_width = x2 - x1

                    #box_area = (x2 - x1) * (y2 - y1)

                    if cls == 0 and (box_height >= min_person_size or box_width >= min_person_size):
                        bbox_center_x = (x1 + x2) // 2
                        if not (left_person_boundary <= bbox_center_x <= right_person_boundary):
                            continue

                        person_detected = True
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, "Person", (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            if custom_results:
                custom_conf_threshold = custom_conf or self.custom_default_conf
                raw_detections = []
                for model_info, result_batch in custom_results:
                    names = model_info.get("names", {})
                    for result in result_batch:
                        for box in result.boxes:
                            cls = int(box.cls[0])
                            conf = float(box.conf[0]) if hasattr(box, "conf") else 0.0
                            if conf < custom_conf_threshold:
                                continue
                            x1, y1, x2, y2 = map(float, box.xyxy[0])
                            box_height = y2 - y1
                            box_width = x2 - x1

                            label = self._get_custom_label(cls, names)
                            min_threshold = custom_size_thresholds.get(label, 0.0)
                            if max(box_height, box_width) < min_threshold:
                                continue
                            raw_detections.append(
                                {
                                    "cls": cls,
                                    "conf": conf,
                                    "box": (x1, y1, x2, y2),
                                    "label": label,
                                }
                            )

                merged_detections = self._merge_custom_detections(
                    raw_detections, CUSTOM_NMS_IOU_THRESHOLD
                )

                for detection in merged_detections:
                    x1, y1, x2, y2 = map(int, detection["box"])
                    label = detection["label"]
                    min_size_threshold = custom_size_thresholds.get(label, 0.0)
                    box_height = y2 - y1
                    box_width = x2 - x1
                    if max(box_height, box_width) < min_size_threshold:
                        continue
                    if label == "SEMAFORO":
                        roi = frame[y1:y2, x1:x2]
                        active_color, color_bgr, traffic_light_state = process_traffic_light_roi(roi)

                        y_div1 = y1 + box_height // 3
                        y_div2 = y1 + 2 * (box_height // 3)

                        cv2.line(frame, (x1, y_div1), (x2, y_div1), (255, 255, 255), 1)
                        cv2.line(frame, (x1, y_div2), (x2, y_div2), (255, 255, 255), 1)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color_bgr, 2)
                        cv2.putText(
                            frame,
                            f"TL: {active_color}",
                            (x1, y1 - 20),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            color_bgr,
                            2,
                        )
                        detected_custom_labels.add(label)
                        continue

                    detected_custom_labels.add(label)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), CUSTOM_BOX_COLOR, 2)
                    cv2.putText(
                        frame,
                        label,
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        CUSTOM_BOX_COLOR,
                        2,
                    )

            return person_detected, traffic_light_state, detected_custom_labels

        except Exception as e:
            self.logger.error(f"Erro ao processar frame: {e}")

    @staticmethod
    def _merge_custom_detections(detections, iou_threshold):
        if not detections:
            return []

        grouped = defaultdict(list)
        for det in detections:
            grouped[det["cls"]].append(det)

        merged = []
        for cls, det_list in grouped.items():
            det_list.sort(key=lambda item: item["conf"], reverse=True)
            while det_list:
                current = det_list.pop(0)
                merged.append(current)
                remaining = []
                for candidate in det_list:
                    if ObjectDetector._iou(current["box"], candidate["box"]) < iou_threshold:
                        remaining.append(candidate)
                det_list = remaining
        return merged

    @staticmethod
    def _iou(box_a, box_b):
        ax1, ay1, ax2, ay2 = box_a
        bx1, by1, bx2, by2 = box_b

        inter_x1 = max(ax1, bx1)
        inter_y1 = max(ay1, by1)
        inter_x2 = min(ax2, bx2)
        inter_y2 = min(ay2, by2)

        if inter_x2 <= inter_x1 or inter_y2 <= inter_y1:
            return 0.0

        inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
        area_a = max(0.0, (ax2 - ax1)) * max(0.0, (ay2 - ay1))
        area_b = max(0.0, (bx2 - bx1)) * max(0.0, (by2 - by1))

        union_area = area_a + area_b - inter_area
        if union_area <= 0:
            return 0.0

        return inter_area / union_area

    def cleanup(self):
        if self.video_processor:
            self.video_processor.release()
        cv2.destroyAllWindows()
