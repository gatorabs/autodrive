from __future__ import annotations

import cv2
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap, QResizeEvent
from PySide6.QtWidgets import QLabel, QWidget

from src.presentation.ui.theme.tokens import Color, Radius, Size
from src.presentation.ui.widgets.card import Card


class VideoTile(Card):
    def __init__(self, title: str, placeholder: str, error_key: str, parent: QWidget | None = None):
        super().__init__(title, parent=parent)
        self.placeholder = placeholder
        self.error_key = error_key
        self._source_pixmap: QPixmap | None = None

        self.body_layout.setContentsMargins(6, 0, 6, 6)

        self.status_dot = QLabel(self.header)
        self.status_dot.setFixedSize(10, 10)
        self._set_dot(Color.SUBTLE)
        self.set_accessory(self.status_dot)

        self.image_label = QLabel(placeholder, self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumHeight(Size.VIDEO_MIN_HEIGHT)
        self.image_label.setStyleSheet(
            f"background-color: {Color.PANEL_ALT}; color: {Color.MUTED}; border-radius: {Radius.SM}px;"
        )
        self.body_layout.addWidget(self.image_label, 1)

    def update_state(self, frame, *, webview: bool = False, safe_stop: bool = False, object_safe_stop: bool = False):
        if webview:
            self._show_text("Webview active")
            self._set_dot(Color.WARNING)
            return
        if self.error_key == "lane" and safe_stop:
            self._show_text("Transmission error")
            self._set_dot(Color.DANGER)
            return
        if self.error_key == "object" and object_safe_stop:
            self._show_text("Transmission error")
            self._set_dot(Color.DANGER)
            return
        if frame is None:
            self._show_text(self.placeholder)
            self._set_dot(Color.SUBTLE)
            return
        pixmap = self._to_pixmap(frame)
        if pixmap is None:
            self._show_text(self.placeholder)
            self._set_dot(Color.DANGER)
            return
        self._source_pixmap = pixmap
        self._render()
        self._set_dot(Color.SUCCESS)

    def _set_dot(self, color: str) -> None:
        self.status_dot.setStyleSheet(f"background-color: {color}; border-radius: 5px;")

    @staticmethod
    def _to_pixmap(frame) -> QPixmap | None:
        try:
            if isinstance(frame, (bytes, bytearray)):
                image = QImage.fromData(frame)
                return None if image.isNull() else QPixmap.fromImage(image)
            if isinstance(frame, np.ndarray):
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                height, width, _ = rgb.shape
                stride = rgb.strides[0]
                image = QImage(rgb.data, width, height, stride, QImage.Format.Format_RGB888).copy()
                return QPixmap.fromImage(image)
        except (cv2.error, ValueError):
            return None
        return None

    def _target_size(self) -> tuple[int, int]:
        width = max(240, self.image_label.width() - 2)
        height = max(Size.VIDEO_MIN_HEIGHT, self.image_label.height() - 2)
        target_height = int(width * 9 / 16)
        if target_height > height:
            target_height = height
            width = int(height * 16 / 9)
        return max(1, width), max(1, target_height)

    def _render(self) -> None:
        if self._source_pixmap is None:
            return
        width, height = self._target_size()
        scaled = self._source_pixmap.scaled(
            width, height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self.image_label.setPixmap(scaled)
        self.image_label.setText("")

    def _show_text(self, text: str) -> None:
        self._source_pixmap = None
        self.image_label.setPixmap(QPixmap())
        self.image_label.setText(text)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if self._source_pixmap is not None:
            self._render()
