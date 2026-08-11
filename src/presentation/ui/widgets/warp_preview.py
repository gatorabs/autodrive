from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QCursor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QWidget

from src.domain.constants.calibration_ranges import CAMERA_FRAME_HEIGHT, CAMERA_FRAME_WIDTH
from src.presentation.ui.runtime_constants import WARP_POINT_HIT_RADIUS_PX
from src.presentation.ui.theme.tokens import Color, Radius, Type

IMAGE_WIDTH = CAMERA_FRAME_WIDTH
IMAGE_HEIGHT = CAMERA_FRAME_HEIGHT
_ORDER = ("tl", "tr", "br", "bl")
_LABELS = {"tl": "TL", "tr": "TR", "br": "BR", "bl": "BL"}
_HIT_RADIUS = WARP_POINT_HIT_RADIUS_PX


class WarpPointsPreview(QWidget):
    """Live plot of the 4 warp-perspective corner points over an image-sized
    canvas. Each point can also be dragged directly to change its value."""

    cornerChanged = Signal(str, float, float)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setMinimumHeight(170)
        self.setMouseTracking(True)
        self._points: dict[str, tuple[float, float]] = {
            "tl": (0.0, 0.0),
            "tr": (float(IMAGE_WIDTH), 0.0),
            "bl": (0.0, float(IMAGE_HEIGHT)),
            "br": (float(IMAGE_WIDTH), float(IMAGE_HEIGHT)),
        }
        self._dragging: str | None = None
        self._hovered: str | None = None

    def set_points(self, tl: tuple, tr: tuple, bl: tuple, br: tuple) -> None:
        if self._dragging is not None:
            return
        self._points = {"tl": tl, "tr": tr, "bl": bl, "br": br}
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

    def _to_widget(self, point: tuple, rect: QRectF) -> QPointF:
        px_x = max(0.0, min(float(point[0]), IMAGE_WIDTH))
        px_y = max(0.0, min(float(point[1]), IMAGE_HEIGHT))
        return QPointF(
            rect.left() + px_x / IMAGE_WIDTH * rect.width(),
            rect.top() + px_y / IMAGE_HEIGHT * rect.height(),
        )

    def _to_image(self, pos: QPointF, rect: QRectF) -> tuple[float, float]:
        x = (pos.x() - rect.left()) / rect.width() * IMAGE_WIDTH if rect.width() else 0.0
        y = (pos.y() - rect.top()) / rect.height() * IMAGE_HEIGHT if rect.height() else 0.0
        return max(0.0, min(x, IMAGE_WIDTH)), max(0.0, min(y, IMAGE_HEIGHT))

    def _corner_at(self, pos: QPointF, rect: QRectF) -> str | None:
        best_key, best_dist = None, _HIT_RADIUS
        for key in _ORDER:
            widget_pt = self._to_widget(self._points[key], rect)
            dist = (widget_pt - pos).manhattanLength()
            if dist <= best_dist:
                best_key, best_dist = key, dist
        return best_key

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

        widget_points = {key: self._to_widget(self._points[key], rect) for key in _ORDER}
        polygon_points = [widget_points[key] for key in _ORDER]

        fill_color = QColor(Color.PRIMARY)
        fill_color.setAlpha(40)
        painter.setBrush(fill_color)
        outline_pen = QPen(QColor(Color.PRIMARY))
        outline_pen.setWidthF(2)
        painter.setPen(outline_pen)
        painter.drawPolygon(QPolygonF(polygon_points))

        label_font = painter.font()
        label_font.setPointSize(max(7, Type.CAPTION - 2))
        label_font.setBold(True)
        painter.setFont(label_font)

        for key in _ORDER:
            point = widget_points[key]
            active = key == self._dragging or key == self._hovered
            radius = 6.5 if active else 4.5
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(Color.TEXT if active else Color.PRIMARY))
            painter.drawEllipse(point, radius, radius)
            painter.setPen(QColor(Color.TEXT))
            painter.drawText(point + QPointF(6, -6), _LABELS[key])

        painter.end()

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        rect = self._canvas_rect()
        corner = self._corner_at(event.position(), rect)
        if corner is not None:
            self._dragging = corner
            self.update()

    def mouseMoveEvent(self, event) -> None:
        rect = self._canvas_rect()
        if self._dragging is not None:
            x, y = self._to_image(event.position(), rect)
            x, y = round(x), round(y)
            self._points[self._dragging] = (x, y)
            self.update()
            self.cornerChanged.emit(self._dragging, x, y)
            return
        hovered = self._corner_at(event.position(), rect)
        if hovered != self._hovered:
            self._hovered = hovered
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor if hovered else Qt.CursorShape.ArrowCursor))
            self.update()

    def mouseReleaseEvent(self, event) -> None:
        if self._dragging is not None:
            self._dragging = None
            self.update()

    def leaveEvent(self, event) -> None:
        if self._hovered is not None:
            self._hovered = None
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            self.update()
