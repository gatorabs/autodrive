from pathlib import Path

import cv2
from ultralytics import YOLO
import torch
from src.infrastructure.services.object_detection_service import process_traffic_light_roi
from src.infrastructure.adapters.video.video_process import VideoProcessor
from src.infrastructure.constants.video_constants import (
    FRAME_WIDTH,
    FRAME_HEIGHT,
)

from .custom_model_utils import load_names_from_metadata, normalise_names_payload

TARGET_CLASSES = {0, 9}
DEFAULT_CUSTOM_MODEL_PATH = Path("runs/detect/train/weights/best.pt")
DEFAULT_CUSTOM_LABEL = "Custom Object"
DEFAULT_CUSTOM_CONFIDENCE = 0.45
CUSTOM_MIN_SIZE_KEY = "Ex1"
CUSTOM_CONF_KEY = "Ex2"
CUSTOM_BOX_COLOR = (255, 140, 0)
PERSON_REGION_WIDTH_KEY = "PeopleRegion"
DEFAULT_PERSON_REGION_PERCENT = 33
DEFAULT_PREPROCESS_SIZE = 640


def preprocess_bchw(frame, size=DEFAULT_PREPROCESS_SIZE, device="cuda", fp16=True):
    import cv2  # local import to align with helper guidance
    import numpy as np
    import torch

    h, w = frame.shape[:2]
    r = min(size / h, size / w)
    new_unpad = (int(round(w * r)), int(round(h * r)))
    dw, dh = size - new_unpad[0], size - new_unpad[1]
    dw //= 2
    dh //= 2

    img = cv2.resize(frame, new_unpad, interpolation=cv2.INTER_LINEAR)
    img = cv2.copyMakeBorder(
        img,
        dh,
        size - new_unpad[1] - dh,
        dw,
        size - new_unpad[0] - dw,
        cv2.BORDER_CONSTANT,
        value=(114, 114, 114),
    )
    img = img[:, :, ::-1]
    img = img.transpose(2, 0, 1)
    img = np.ascontiguousarray(img)
    tensor = torch.from_numpy(img).to(device)
    tensor = tensor.float().div_(255.0).unsqueeze(0)
    if fp16:
        tensor = tensor.half()
    return tensor

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

        self.preprocess_size = DEFAULT_PREPROCESS_SIZE
        self.inference_kwargs = {
            "classes": list(TARGET_CLASSES),
            "verbose": False,
            "conf": 0.4,
            "max_det": 100,
            "iou": 0.6,
        }

        if self.device == "cuda":
            self.inference_kwargs["half"] = True  # FP16 na GPU
        else:
            self.inference_kwargs["imgsz"] = self.preprocess_size

        self.custom_models = []
        self.custom_default_label = DEFAULT_CUSTOM_LABEL
        self.custom_default_conf = DEFAULT_CUSTOM_CONFIDENCE
        self.custom_inference_kwargs = {
            "verbose": False,
            "max_det": 100,
            "iou": 0.6,
        }

        if self.device == "cuda":
            self.custom_inference_kwargs["half"] = True
        else:
            self.custom_inference_kwargs["imgsz"] = self.preprocess_size

        self._load_custom_models()
        self._warmup_models()

        self.shared_serial_data[1] = 0  # semáforo
        self.shared_serial_data[2] = 0  # pessoa
        if len(self.shared_serial_data) > 0:
            self.shared_serial_data[0] = 0  # objeto customizado

        if PERSON_REGION_WIDTH_KEY not in self.tk_controls:
            self.tk_controls[PERSON_REGION_WIDTH_KEY] = DEFAULT_PERSON_REGION_PERCENT

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

        for model_path in model_paths:
            try:
                model = YOLO(str(model_path))
                model.to(self.device)
                model.eval()

                names_payload = normalise_names_payload(getattr(model, "names", {}))
                if not names_payload:
                    names_payload = load_names_from_metadata(model_path)

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

    def process_frame(self, frame):
        try:
            tensor_bchw = preprocess_bchw(
                frame,
                size=self.preprocess_size,
                device=self.device,
                fp16=self.device == "cuda",
            )
            with torch.inference_mode():
                results = self.model(tensor_bchw, **self.inference_kwargs)
                custom_results = []
                if self.custom_models:
                    custom_conf = self._get_custom_confidence()
                    for custom_model in self.custom_models:
                        model = custom_model["model"]
                        model_results = model(
                            tensor_bchw,
                            conf=custom_conf,
                            **self.custom_inference_kwargs,
                        )
                        custom_results.append((custom_model, model_results))

            person_detected = False
            traffic_light_state = 2
            custom_object_detected = False

            min_person_size = self.tk_controls["Person"]
            min_traffic_size = self.tk_controls["Traffic"]
            min_custom_size = self.tk_controls.get(CUSTOM_MIN_SIZE_KEY, 0)

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

                    elif cls == 9 and (box_height >= min_traffic_size or box_width >= min_traffic_size):
                        roi = frame[y1:y2, x1:x2]
                        active_color, color_bgr, traffic_light_state = process_traffic_light_roi(roi)

                        y_div1 = y1 + box_height // 3
                        y_div2 = y1 + 2 * (box_height // 3)

                        cv2.line(frame, (x1, y_div1), (x2, y_div1), (255, 255, 255), 1)
                        cv2.line(frame, (x1, y_div2), (x2, y_div2), (255, 255, 255), 1)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color_bgr, 2)
                        cv2.putText(frame, f"TL: {active_color}", (x1, y1 - 20),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_bgr, 2)

            if custom_results:
                for model_info, result_batch in custom_results:
                    names = model_info.get("names", {})
                    for result in result_batch:
                        for box in result.boxes:
                            cls = int(box.cls[0])
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            box_height = y2 - y1
                            box_width = x2 - x1

                            if max(box_height, box_width) < min_custom_size:
                                continue

                            custom_object_detected = True
                            label = self._get_custom_label(cls, names)
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

            return person_detected, traffic_light_state, custom_object_detected

        except Exception as e:
            self.logger.error(f"Erro ao processar frame: {e}")

    def cleanup(self):
        if self.video_processor:
            self.video_processor.release()
        cv2.destroyAllWindows()

    def _warmup_models(self):
        if self.device != "cuda":
            return

        dummy = torch.zeros(
            1,
            3,
            self.preprocess_size,
            self.preprocess_size,
            device=self.device,
        ).half()
        try:
            for _ in range(10):
                self.model(dummy, **self.inference_kwargs)
            for custom_model in self.custom_models:
                model = custom_model.get("model")
                if model is None:
                    continue
                for _ in range(10):
                    model(
                        dummy,
                        conf=self.custom_default_conf,
                        **self.custom_inference_kwargs,
                    )
            torch.cuda.synchronize()
        except Exception as exc:
            if self.logger:
                self.logger.warning(f"Falha no aquecimento dos modelos: {exc}")
