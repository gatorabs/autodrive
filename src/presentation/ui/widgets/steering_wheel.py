from __future__ import annotations

import math

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from src.presentation.ui.theme.tokens import Color


class SteeringWheel(QWidget):
    angleChanged = Signal(int)

    SIZE = 170
    RADIUS = 68
    CENTER = 85

    def __init__(self, angle: float = 90, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedSize(self.SIZE, self.SIZE)
        self._angle = angle

    def set_angle(self, angle: float) -> None:
        self._angle = angle
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx = cy = self.CENTER

        rim_pen = QPen(QColor(Color.SECONDARY))
        rim_pen.setWidth(3)
        painter.setPen(rim_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(cx - self.RADIUS, cy - self.RADIUS, self.RADIUS * 2, self.RADIUS * 2)

        tick_pen = QPen(QColor(Color.BORDER_STRONG))
        tick_pen.setWidth(2)
        painter.setPen(tick_pen)
        for tick_angle in range(0, 181, 30):
            rad = math.radians(tick_angle - 90)
            x1 = cx + (self.RADIUS - 8) * math.cos(rad)
            y1 = cy + (self.RADIUS - 8) * math.sin(rad)
            x2 = cx + (self.RADIUS + 1) * math.cos(rad)
            y2 = cy + (self.RADIUS + 1) * math.sin(rad)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        hub_pen = QPen(QColor(Color.BORDER_STRONG))
        hub_pen.setWidth(1)
        painter.setPen(hub_pen)
        painter.setBrush(QColor(Color.PANEL_ALT))
        painter.drawEllipse(cx - 28, cy - 28, 56, 56)

        rad = math.radians(float(self._angle) - 90)
        x = cx + self.RADIUS * 0.75 * math.cos(rad)
        y = cy + self.RADIUS * 0.75 * math.sin(rad)
        pointer_pen = QPen(QColor(Color.SECONDARY))
        pointer_pen.setWidth(4)
        pointer_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pointer_pen)
        painter.drawLine(cx, cy, int(x), int(y))

        knob_pen = QPen(QColor(Color.PANEL_ALT))
        knob_pen.setWidth(2)
        painter.setPen(knob_pen)
        painter.setBrush(QColor(Color.SECONDARY))
        painter.drawEllipse(int(x) - 7, int(y) - 7, 14, 14)
        painter.end()

    def mouseMoveEvent(self, event) -> None:
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        pos = event.position()
        dx = pos.x() - self.CENTER
        dy = pos.y() - self.CENTER
        angle = int((math.degrees(math.atan2(dy, dx)) + 90) % 180)
        self._angle = angle
        self.update()
        self.angleChanged.emit(angle)
