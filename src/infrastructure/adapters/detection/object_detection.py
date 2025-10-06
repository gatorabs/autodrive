import os
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

TARGET_CLASSES = {0, 9}
CUSTOM_MODEL_ENV_VAR = "CUSTOM_OBJECT_MODEL_PATH"
DEFAULT_CUSTOM_MODEL_PATH = Path("runs/detect/train/weights/best.pt")
CUSTOM_LABEL_ENV_VAR = "CUSTOM_OBJECT_LABEL"
CUSTOM_CONF_ENV_VAR = "CUSTOM_OBJECT_CONFIDENCE"
CUSTOM_MIN_SIZE_KEY = "Ex1"
CUSTOM_CONF_KEY = "Ex2"
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

        self.custom_model = None
        self.custom_model_names = {}
        self.custom_default_label = os.getenv(CUSTOM_LABEL_ENV_VAR, "Custom Object")
        self.custom_default_conf = self._parse_env_confidence()
        self.custom_inference_kwargs = {
            "verbose": False,
        }

        if self.device == "cuda":
            self.custom_inference_kwargs["half"] = True
        else:
            self.custom_inference_kwargs["imgsz"] = CPU_INFERENCE_IMG_SIZE

        self._load_custom_model()

        self.shared_serial_data[1] = 0  # semáforo
        self.shared_serial_data[2] = 0  # pessoa
        if len(self.shared_serial_data) > 0:
            self.shared_serial_data[0] = 0  # objeto customizado

    def _parse_env_confidence(self):
        env_value = os.getenv(CUSTOM_CONF_ENV_VAR)
        if env_value is None:
            return 0.35
        try:
            return max(0.05, min(0.99, float(env_value)))
        except ValueError:
            if self.logger:
                self.logger.warning(
                    f"Valor inválido para {CUSTOM_CONF_ENV_VAR}: {env_value}. Usando 0.35.")
            return 0.35

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

    def _find_latest_trained_model(self, search_roots):
        matches = []
        for root in search_roots:
            try:
                for possible in root.glob("**/runs/detect/*/weights/best.pt"):
                    if possible.exists():
                        matches.append(possible)
            except Exception:
                continue

        if not matches:
            return None

        try:
            matches.sort(key=lambda path: path.stat().st_mtime, reverse=True)
        except OSError:
            pass

        return matches[0]

    def _resolve_custom_model_path(self):
        configured_path = os.getenv(CUSTOM_MODEL_ENV_VAR)
        search_roots = self._candidate_search_roots()

        if configured_path:
            configured = Path(configured_path)
            if configured.is_absolute():
                return configured

            for root in search_roots:
                potential = root / configured
                if potential.exists():
                    return potential

            return search_roots[0] / configured

        candidate = DEFAULT_CUSTOM_MODEL_PATH

        if candidate.is_absolute():
            return candidate

        for root in search_roots:
            potential = root / candidate
            if potential.exists():
                return potential

        fallback = self._find_latest_trained_model(search_roots)
        if fallback:
            if self.logger:
                self.logger.info(
                    f"Modelo padrão não encontrado em {search_roots[0] / candidate}. Usando {fallback}.")
            return fallback

        return search_roots[0] / candidate

    def _load_custom_model(self):
        model_path = self._resolve_custom_model_path()
        if not model_path:
            return

        if not model_path.exists():
            if self.logger:
                self.logger.info(
                    f"Modelo customizado não encontrado em {model_path}. Detecção extra desativada.")
            return

        try:
            self.custom_model = YOLO(str(model_path))
            self.custom_model.to(self.device)
            self.custom_model.eval()
            names = getattr(self.custom_model, "names", {})
            self.custom_model_names = names if isinstance(names, (dict, list)) else {}
            if self.logger:
                self.logger.info(f"Modelo customizado carregado de {model_path}")
        except Exception as exc:
            if self.logger:
                self.logger.error(f"Falha ao carregar modelo customizado ({model_path}): {exc}")
            self.custom_model = None

    def _get_custom_label(self, cls_id):
        names = self.custom_model_names
        if isinstance(names, dict):
            return names.get(cls_id, self.custom_default_label)
        if isinstance(names, list) and 0 <= cls_id < len(names):
            return names[cls_id]
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
            with torch.inference_mode():
                results = self.model(frame, **self.inference_kwargs)
                custom_results = None
                if self.custom_model is not None:
                    custom_conf = self._get_custom_confidence()
                    custom_results = self.custom_model(
                        frame,
                        conf=custom_conf,
                        **self.custom_inference_kwargs,
                    )

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

            if custom_results is not None:
                for result in custom_results:
                    for box in result.boxes:
                        cls = int(box.cls[0])
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        box_height = y2 - y1
                        box_width = x2 - x1

                        if max(box_height, box_width) < min_custom_size:
                            continue

                        custom_object_detected = True
                        label = self._get_custom_label(cls)
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
