from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QSplitter, QSplitterHandle, QWidget

from src.presentation.ui.theme.tokens import Color

_GRIP_LENGTH = 44
_GRIP_THICKNESS = 4


class _GripHandle(QSplitterHandle):
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(Color.BG))

        color = Color.PRIMARY if self.underMouse() else Color.BORDER_STRONG
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(color))

        center = self.rect().center()
        if self.orientation() == Qt.Orientation.Vertical:
            grip = QRectF(center.x() - _GRIP_LENGTH / 2, center.y() - _GRIP_THICKNESS / 2, _GRIP_LENGTH, _GRIP_THICKNESS)
        else:
            grip = QRectF(center.x() - _GRIP_THICKNESS / 2, center.y() - _GRIP_LENGTH / 2, _GRIP_THICKNESS, _GRIP_LENGTH)
        painter.drawRoundedRect(grip, _GRIP_THICKNESS / 2, _GRIP_THICKNESS / 2)
        painter.end()

    def enterEvent(self, event) -> None:
        super().enterEvent(event)
        self.update()

    def leaveEvent(self, event) -> None:
        super().leaveEvent(event)
        self.update()


class ElegantSplitter(QSplitter):
    """QSplitter with a minimal centered grip instead of a full-width bar."""

    def __init__(self, orientation: Qt.Orientation, parent: QWidget | None = None):
        super().__init__(orientation, parent)
        self.setHandleWidth(12)

    def createHandle(self) -> QSplitterHandle:
        return _GripHandle(self.orientation(), self)
