from pathlib import Path

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

from .custom_model_utils import load_names_from_metadata, normalise_names_payload

TARGET_CLASSES = {0, 9}
DEFAULT_CUSTOM_MODEL_PATH = Path("runs/detect/train/weights/best.pt")
DEFAULT_CUSTOM_LABEL = "Custom Object"
DEFAULT_CUSTOM_CONFIDENCE = 0.35
CUSTOM_MIN_SIZE_KEY = "Ex1"
CUSTOM_CONF_KEY = "Ex2"
CUSTOM_CONF_OVERRIDES_KEY = "CUSTOM_CONF_OVERRIDES"
CUSTOM_CONF_METADATA_KEY = "CUSTOM_CONF_METADATA"
CUSTOM_CONF_DEFAULT_KEY = "CUSTOM_CONF_DEFAULT"
CUSTOM_BOX_COLOR = (255, 140, 0)

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
        self.custom_inference_kwargs = {
            "verbose": False,
        }

        if self.device == "cuda":
            self.custom_inference_kwargs["half"] = True
        else:
            self.custom_inference_kwargs["imgsz"] = CPU_INFERENCE_IMG_SIZE

        self._load_custom_models()
        self._publish_custom_conf_metadata()

        self.shared_serial_data[1] = 0  # semáforo
        self.shared_serial_data[2] = 0  # pessoa
        if len(self.shared_serial_data) > 0:
            self.shared_serial_data[0] = 0  # objeto customizado

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

                conf_keys = {}
                for cls_id in names_payload:
                    conf_keys[int(cls_id)] = self._build_conf_key(model_path, int(cls_id))

                self.custom_models.append({
                    "model": model,
                    "names": names_payload,
                    "path": model_path,
                    "conf_keys": conf_keys,
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

    def _build_conf_key(self, model_path: Path, cls_id: int) -> str:
        try:
            resolved = model_path.resolve()
        except OSError:
            resolved = model_path
        return f"{resolved.as_posix()}::{cls_id}"

    def _publish_custom_conf_metadata(self):
        metadata = {}
        raw_overrides = self.tk_controls.get(CUSTOM_CONF_OVERRIDES_KEY, {})
        overrides = dict(raw_overrides) if isinstance(raw_overrides, dict) else {}
        changed_overrides = False

        for custom_model in self.custom_models:
            model_path: Path = custom_model.get("path")
            if not isinstance(model_path, Path):
                model_path = Path(model_path)
            run_name = None
            try:
                run_name = model_path.parent.parent.name
            except Exception:
                run_name = model_path.stem
            if not run_name:
                run_name = model_path.stem

            for cls_id, label in custom_model.get("names", {}).items():
                safe_label = str(label) if label is not None else f"cls_{cls_id}"
                key = custom_model.get("conf_keys", {}).get(int(cls_id))
                if not key:
                    key = self._build_conf_key(model_path, int(cls_id))
                    custom_model.setdefault("conf_keys", {})[int(cls_id)] = key
                metadata[key] = {
                    "label": safe_label,
                    "model": str(run_name) if run_name else "",
                }
                if key not in overrides:
                    overrides[key] = self.custom_default_conf
                    changed_overrides = True

        stale_keys = set(overrides.keys()) - set(metadata.keys())
        if stale_keys:
            for key in stale_keys:
                overrides.pop(key, None)
            changed_overrides = True

        self.tk_controls[CUSTOM_CONF_METADATA_KEY] = metadata
        self.tk_controls[CUSTOM_CONF_DEFAULT_KEY] = self.custom_default_conf
        if changed_overrides or self.tk_controls.get(CUSTOM_CONF_OVERRIDES_KEY) != overrides:
            self.tk_controls[CUSTOM_CONF_OVERRIDES_KEY] = overrides

    def _get_custom_confidence(self):
        slider_value = self.tk_controls.get(CUSTOM_CONF_KEY)
        if slider_value is None:
            base_conf = self.custom_default_conf
        else:
            try:
                base_conf = max(0.05, min(0.99, float(slider_value) / 10.0))
            except (TypeError, ValueError):
                base_conf = self.custom_default_conf

        overrides = self.tk_controls.get(CUSTOM_CONF_OVERRIDES_KEY, {})
        if isinstance(overrides, dict) and overrides:
            try:
                min_override = min(
                    max(0.05, min(0.99, float(value)))
                    for value in overrides.values()
                )
            except (TypeError, ValueError):
                min_override = None
            if min_override is not None:
                return min(base_conf, min_override)
        return base_conf

    def _resolve_conf_threshold(self, model_info: dict, cls_id: int) -> float:
        overrides = self.tk_controls.get(CUSTOM_CONF_OVERRIDES_KEY, {})
        if not isinstance(overrides, dict):
            overrides = {}

        conf_keys = model_info.get("conf_keys", {})
        key = conf_keys.get(int(cls_id)) if isinstance(conf_keys, dict) else None
        if key:
            try:
                value = float(overrides.get(key, self.custom_default_conf))
            except (TypeError, ValueError):
                value = self.custom_default_conf
            return max(0.05, min(0.99, value))
        return self.custom_default_conf

    def process_frame(self, frame):
        try:
            with torch.inference_mode():
                results = self.model(frame, **self.inference_kwargs)
                custom_results = []
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
            custom_object_detected = False

            min_person_size = self.tk_controls["Person"]
            min_traffic_size = self.tk_controls["Traffic"]
            min_custom_size = self.tk_controls.get(CUSTOM_MIN_SIZE_KEY, 0)

            for result in results:
                for box in result.boxes:
                    cls = int(box.cls[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    box_height = y2 - y1
                    box_width = x2 - x1

                    #box_area = (x2 - x1) * (y2 - y1)

                    if cls == 0 and (box_height >= min_person_size or box_width >= min_person_size):
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
                            threshold = self._resolve_conf_threshold(model_info, cls)
                            try:
                                confidence = float(box.conf[0])
                            except (TypeError, ValueError, IndexError):
                                confidence = 0.0
                            if confidence < threshold:
                                continue
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
                                f"{label} ({confidence:.2f})",
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
