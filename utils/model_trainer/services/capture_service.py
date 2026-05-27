from __future__ import annotations

import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import yaml


def slugify(value: str, fallback: str) -> str:
    value = re.sub(r"[^0-9a-zA-Z_-]+", "-", value.strip())
    value = re.sub(r"-+", "-", value).strip("-_")
    return value or fallback


def bbox_to_yolo(x: int, y: int, width: int, height: int, img_width: int, img_height: int):
    return (
        (x + width / 2) / img_width,
        (y + height / 2) / img_height,
        width / img_width,
        height / img_height,
    )


def bbox_inside_frame(
    img_width: int,
    img_height: int,
    x: int,
    y: int,
    width: int,
    height: int,
    margin: int = 2,
) -> bool:
    return (
        x >= margin
        and y >= margin
        and x + width <= img_width - margin
        and y + height <= img_height - margin
        and width > 4
        and height > 4
    )


def frame_sharpness(frame) -> float:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def create_tracker():
    if hasattr(cv2, "legacy"):
        for factory_name in ("TrackerCSRT_create", "TrackerKCF_create", "TrackerMOSSE_create"):
            factory = getattr(cv2.legacy, factory_name, None)
            if factory is not None:
                return factory()
    for factory_name in ("TrackerCSRT_create", "TrackerKCF_create", "TrackerMOSSE_create"):
        factory = getattr(cv2, factory_name, None)
        if factory is not None:
            return factory()
    raise RuntimeError("OpenCV tracker API is unavailable. Install opencv-contrib-python to enable tracking.")


@dataclass(frozen=True)
class CaptureTarget:
    class_name: str
    class_id: int
    root: Path

    @property
    def images_dir(self) -> Path:
        return self.root / "images"

    @property
    def labels_dir(self) -> Path:
        return self.root / "labels"


class CameraCaptureSession:
    def __init__(
        self,
        *,
        camera_index: int,
        target: CaptureTarget,
        target_fps: float = 2.0,
        save_when_no_box: bool = False,
    ) -> None:
        self.camera_index = camera_index
        self.target = target
        self.target_fps = max(0.1, float(target_fps))
        self.save_when_no_box = save_when_no_box
        self.capture = None
        self.tracker = None
        self.tracking = False
        self.recording = False
        self.bbox: tuple[int, int, int, int] | None = None
        self.previous_center: tuple[float, float] | None = None
        self.last_save = 0.0
        self.saved_count = 0
        self.last_frame = None
        self.status = "Camera closed"

    @property
    def save_interval(self) -> float:
        return 1.0 / self.target_fps

    def open(self) -> None:
        self.target.images_dir.mkdir(parents=True, exist_ok=True)
        self.target.labels_dir.mkdir(parents=True, exist_ok=True)
        self.capture = cv2.VideoCapture(self.camera_index)
        if not self.capture.isOpened():
            self.capture.release()
            self.capture = None
            raise RuntimeError(f"Camera {self.camera_index} is unavailable.")
        self.status = "Camera opened"

    def close(self) -> None:
        if self.capture is not None:
            self.capture.release()
        self.capture = None
        self.tracker = None
        self.tracking = False
        self.recording = False
        self.status = "Camera closed"

    def set_bbox(self, bbox: tuple[int, int, int, int]) -> None:
        x, y, width, height = bbox
        self.bbox = (int(x), int(y), max(1, int(width)), max(1, int(height)))
        self.tracker = None
        self.tracking = False
        self.previous_center = None
        self.status = "Bounding box ready"

    def clear_bbox(self) -> None:
        self.bbox = None
        self.tracker = None
        self.tracking = False
        self.previous_center = None
        self.status = "Bounding box cleared"

    def start_tracking(self) -> None:
        if self.last_frame is None or self.bbox is None:
            raise RuntimeError("Set a bounding box before starting tracking.")
        self.tracker = create_tracker()
        self.tracker.init(self.last_frame, self.bbox)
        self.tracking = True
        self.previous_center = None
        self.status = "Tracking active"

    def stop_tracking(self) -> None:
        self.tracker = None
        self.tracking = False
        self.previous_center = None
        self.status = "Tracking stopped"

    def set_recording(self, enabled: bool) -> None:
        self.recording = bool(enabled)
        self.last_save = 0.0
        self.status = "Recording active" if enabled else "Recording stopped"

    def read(self):
        if self.capture is None:
            return None
        ok, frame = self.capture.read()
        if not ok:
            self.status = "Camera frame unavailable"
            return None

        self.last_frame = frame
        self._update_tracking(frame)
        if self.recording:
            self._auto_save(frame)
        return frame

    def draw_overlay(self, frame):
        output = frame.copy()
        if self.bbox is not None:
            x, y, width, height = self.bbox
            color = (0, 255, 0) if self.tracking else (255, 180, 0)
            cv2.rectangle(output, (x, y), (x + width, y + height), color, 2)
            cv2.putText(
                output,
                "tracking" if self.tracking else "bbox ready",
                (x, max(18, y - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                color,
                2,
            )

        cv2.putText(
            output,
            f"{self.target.class_name} | saved={self.saved_count} | {self.status}",
            (12, 26),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
        )
        return output

    def save_current_frame(self) -> Path | None:
        if self.last_frame is None:
            return None
        return self._save_frame(self.last_frame, self.bbox)

    def generate_data_yaml(self) -> Path:
        yaml_path = self.target.root / "data.yaml"
        names = [f"classe_{idx:02d}" for idx in range(self.target.class_id + 1)]
        names[self.target.class_id] = self.target.class_name
        payload = {
            "path": str(self.target.root.resolve()),
            "train": "images",
            "val": "images",
            "names": names,
        }
        yaml_path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
        return yaml_path

    def _update_tracking(self, frame) -> None:
        if not self.tracking or self.tracker is None:
            return

        ok, bbox = self.tracker.update(frame)
        if not ok:
            self.recording = False
            self.tracking = False
            self.tracker = None
            self.status = "Tracking lost"
            return

        self.bbox = tuple(int(value) for value in bbox)
        self.status = "Tracking active"

    def _auto_save(self, frame) -> None:
        now = time.time()
        if now - self.last_save < self.save_interval:
            return
        if self._is_current_bbox_stable(frame) or self.save_when_no_box:
            self._save_frame(frame, self.bbox)
            self.last_save = now

    def _is_current_bbox_stable(self, frame) -> bool:
        if self.bbox is None:
            return False
        height, width = frame.shape[:2]
        x, y, box_width, box_height = self.bbox
        if not bbox_inside_frame(width, height, x, y, box_width, box_height):
            return False

        sharp_ok = frame_sharpness(frame) > 60
        center = (x + box_width / 2, y + box_height / 2)
        jump = 0.0
        if self.previous_center is not None:
            jump = float(np.hypot(center[0] - self.previous_center[0], center[1] - self.previous_center[1]))
        self.previous_center = center
        jump_ok = jump < max(box_width, box_height) * 0.35
        return sharp_ok and jump_ok

    def _save_frame(self, frame, bbox: tuple[int, int, int, int] | None) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        image_path = self.target.images_dir / f"{timestamp}.jpg"
        label_path = self.target.labels_dir / f"{timestamp}.txt"

        cv2.imwrite(str(image_path), frame)
        if bbox is not None:
            img_height, img_width = frame.shape[:2]
            x, y, width, height = bbox
            xc, yc, wn, hn = bbox_to_yolo(x, y, width, height, img_width, img_height)
            label_path.write_text(
                f"{self.target.class_id} {xc:.6f} {yc:.6f} {wn:.6f} {hn:.6f}\n",
                encoding="utf-8",
            )
        else:
            label_path.write_text("", encoding="utf-8")

        self.saved_count += 1
        self.generate_data_yaml()
        self.status = f"Saved {image_path.name}"
        return image_path
