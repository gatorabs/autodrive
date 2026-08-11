from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QWidget

from src.presentation.ui.theme.tokens import Color, Radius, Type

IMAGE_WIDTH = 640
IMAGE_HEIGHT = 480


class WarpPointsPreview(QWidget):
    """Live plot of the 4 warp-perspective corner points over an image-sized
    canvas, so it's clear where each slider actually places its point."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setMinimumHeight(170)
        self._tl = (0.0, 0.0)
        self._tr = (float(IMAGE_WIDTH), 0.0)
        self._bl = (0.0, float(IMAGE_HEIGHT))
        self._br = (float(IMAGE_WIDTH), float(IMAGE_HEIGHT))

    def set_points(self, tl: tuple, tr: tuple, bl: tuple, br: tuple) -> None:
        self._tl, self._tr, self._bl, self._br = tl, tr, bl, br
        self.update()

    def _canvas_rect(self) -> QRectF:
        width, height = self.width(), self.height()
        target_w = width
        target_h = width * IMAGE_HEIGHT / IMAGE_WIDTH
        if target_h > height:
            target_h = height
            target_w = height * IMAGE_WIDTH / IMAGE_HEIGHT
        x = (width - target_w) / 2
        y = (height - target_h) / 2
        return QRectF(x, y, target_w, target_h)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self._canvas_rect()
        if rect.width() <= 0 or rect.height() <= 0:
            painter.end()
            return

        painter.setPen(QPen(QColor(Color.BORDER), 1))
        painter.setBrush(QColor(Color.PANEL_ALT))
        painter.drawRoundedRect(rect, Radius.SM, Radius.SM)

        grid_pen = QPen(QColor(Color.BORDER))
        grid_pen.setWidthF(0.6)
        painter.setPen(grid_pen)
        for i in (1, 2):
            x = rect.left() + rect.width() * i / 3
            painter.drawLine(QPointF(x, rect.top()), QPointF(x, rect.bottom()))
            y = rect.top() + rect.height() * i / 3
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))

        def to_widget(point: tuple) -> QPointF:
            px_x, px_y = point
            px_x = max(0.0, min(float(px_x), IMAGE_WIDTH))
            px_y = max(0.0, min(float(px_y), IMAGE_HEIGHT))
            return QPointF(
                rect.left() + px_x / IMAGE_WIDTH * rect.width(),
                rect.top() + px_y / IMAGE_HEIGHT * rect.height(),
            )

        corners = [to_widget(self._tl), to_widget(self._tr), to_widget(self._br), to_widget(self._bl)]

        fill_color = QColor(Color.PRIMARY)
        fill_color.setAlpha(40)
        painter.setBrush(fill_color)
        outline_pen = QPen(QColor(Color.PRIMARY))
        outline_pen.setWidthF(2)
        painter.setPen(outline_pen)
        painter.drawPolygon(QPolygonF(corners))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(Color.PRIMARY))
        for point in corners:
            painter.drawEllipse(point, 4.5, 4.5)

        label_font = painter.font()
        label_font.setPointSize(max(7, Type.CAPTION - 2))
        label_font.setBold(True)
        painter.setFont(label_font)
        painter.setPen(QColor(Color.TEXT))
        for label, point in zip(("TL", "TR", "BR", "BL"), corners):
            painter.drawText(point + QPointF(6, -6), label)

        painter.end()
