import os
import cv2
from src.infrastructure.constants.video_constants import FRAME_WIDTH, FRAME_HEIGHT, WIDE_CAPTURE_WIDTH, WIDE_CAPTURE_HEIGHT

class VideoProcessor:
    def __init__(self, video_source, frame_width=FRAME_WIDTH, frame_height=FRAME_HEIGHT):
        self.video_source = video_source
        self.output_width = frame_width
        self.output_height = frame_height
        self.internal_width = frame_width
        self.internal_height = frame_height

        self.is_cam = False
        self.cam_index = None

        try:
            self.cam_index = int(video_source)
            self.is_cam = True
        except (TypeError, ValueError):
            self.is_cam = False

        self.is_file = not self.is_cam

        if self.is_cam:
            api = cv2.CAP_DSHOW if os.name == "nt" else cv2.CAP_ANY
            self.cap = cv2.VideoCapture(self.cam_index, api)
        else:
            self.cap = cv2.VideoCapture(video_source)

        if not self.cap.isOpened():
            raise RuntimeError(f"Não foi possível abrir a fonte de vídeo: {video_source}")

        if self.is_cam:
            requested_sizes = [
                (self.output_width, self.output_height),
                (WIDE_CAPTURE_WIDTH, WIDE_CAPTURE_HEIGHT),
            ]

            for width, height in requested_sizes:
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

                actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

                if actual_width == width and actual_height == height:
                    self.internal_width = width
                    self.internal_height = height
                    break
            else:
                actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                self.internal_width = actual_width or self.output_width
                self.internal_height = actual_height or self.output_height

        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self.resize_needed = (
            actual_width != self.output_width or actual_height != self.output_height
        )

    def get_frame(self):
        ret, frame = self.cap.read()

        if not ret:
            if self.is_file:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
                if not ret:
                    raise RuntimeError("Erro ao reiniciar o vídeo")
            else:
                raise RuntimeError("Erro ao capturar frame da câmera")

        if self.resize_needed:
            frame = cv2.resize(frame, (self.output_width, self.output_height), interpolation=cv2.INTER_AREA)

        return frame

    def is_frame_open(self):
        try:
            return self.cap is not None and self.cap.isOpened()
        except Exception:
            return False

    def release(self):
        self.cap.release()
