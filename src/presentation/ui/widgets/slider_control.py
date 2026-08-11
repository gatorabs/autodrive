from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtCore import QPoint, QPointF, QRect, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import QLineEdit, QWidget

from src.presentation.ui.theme.tokens import Color, Radius, Type


@dataclass(frozen=True)
class SliderSpec:
    key: str
    label: str
    min_value: float
    max_value: float
    step: float = 1.0


_ACCENT_TRACKS = {
    "primary": (Color.PRIMARY, "#5eead4", "#99f6e4"),
    "secondary": (Color.SECONDARY, "#c4b5fd", "#ddd6fe"),
    "success": (Color.SUCCESS, "#86efac", "#bbf7d0"),
}


class _InlineEditor(QLineEdit):
    escapePressed = Signal()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.escapePressed.emit()
            return
        super().keyPressEvent(event)


class SliderControl(QWidget):
    TRACK_H = 6
    THUMB_R = 7
    GLOW_R = THUMB_R + 4
    PAD = 4

    def __init__(
        self,
        spec: SliderSpec,
        value: float,
        on_change: Callable[[str, float], None],
        accent: str = "primary",
        height: int = 46,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.spec = spec
        self.on_change = on_change
        self.fill_color, self.thumb_color, self.glow_color = _ACCENT_TRACKS.get(
            accent, _ACCENT_TRACKS["primary"]
        )
        self.setFixedHeight(height)
        self.setMinimumWidth(140)
        self._value = self._normalize(value)
        self._value_rect = QRect()
        self._editor: _InlineEditor | None = None

    def get(self) -> float:
        return self._value

    def set(self, value: float, *, notify: bool = True) -> None:
        self._value = self._normalize(value)
        self.update()
        if notify:
            self.on_change(self.spec.key, self._value)

    def _normalize(self, value: float):
        value = max(self.spec.min_value, min(float(value), self.spec.max_value))
        stepped = round((value - self.spec.min_value) / self.spec.step) * self.spec.step + self.spec.min_value
        return int(round(stepped)) if self.spec.step >= 1 else stepped

    def _format(self, value) -> str:
        return f"{value:.3f}" if self.spec.step < 1 else str(int(round(value)))

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        width, height = self.width(), self.height()

        painter.setFont(QFont(Type.FAMILY, Type.BODY))
        painter.setPen(QColor(Color.MUTED))
        label_rect = QRect(self.PAD, 0, width - self.PAD, 20)
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.spec.label)

        if self._editor is None:
            value_font = QFont(Type.FAMILY, Type.LABEL, QFont.Weight.Bold)
            painter.setFont(value_font)
            painter.setPen(QColor(self.fill_color))
            value_text = self._format(self._value)
            metrics = QFontMetrics(value_font)
            text_width = metrics.horizontalAdvance(value_text)
            value_rect = QRect(width - self.PAD - text_width, 0, text_width, 20)
            painter.drawText(value_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, value_text)
            self._value_rect = value_rect.adjusted(-6, -6, 6, 6)
        else:
            self._value_rect = QRect()

        track_y = height - 13
        left, right = self.THUMB_R + self.PAD, width - self.THUMB_R - self.PAD
        if right <= left:
            painter.end()
            return

        track_pen = QPen(QColor(Color.PANEL_SOFT))
        track_pen.setWidth(self.TRACK_H)
        track_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(track_pen)
        painter.drawLine(left, track_y, right, track_y)

        tick_pen = QPen(QColor(Color.BORDER_STRONG))
        tick_pen.setWidth(1)
        painter.setPen(tick_pen)
        for tick_x in (left, (left + right) / 2, right):
            painter.drawLine(QPointF(tick_x, track_y - 3), QPointF(tick_x, track_y + 3))

        span = self.spec.max_value - self.spec.min_value
        ratio = 0.0 if span <= 0 else (self._value - self.spec.min_value) / span
        thumb_x = left + ratio * (right - left)

        if thumb_x > left:
            fill_pen = QPen(QColor(self.fill_color))
            fill_pen.setWidth(self.TRACK_H)
            fill_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(fill_pen)
            painter.drawLine(QPointF(left, track_y), QPointF(thumb_x, track_y))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(self.glow_color))
        painter.drawEllipse(QPointF(thumb_x, track_y), self.GLOW_R, self.GLOW_R)

        thumb_pen = QPen(QColor(Color.PANEL))
        thumb_pen.setWidth(2)
        painter.setPen(thumb_pen)
        painter.setBrush(QColor(self.thumb_color))
        painter.drawEllipse(QPointF(thumb_x, track_y), self.THUMB_R, self.THUMB_R)
        painter.end()

    def mousePressEvent(self, event) -> None:
        if self._editor is not None:
            return
        self._handle_pointer(event.position().toPoint())

    def mouseMoveEvent(self, event) -> None:
        if self._editor is not None:
            return
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._handle_pointer(event.position().toPoint())

    def _handle_pointer(self, pos: QPoint) -> None:
        if self._value_rect.contains(pos):
            self._begin_edit()
            return
        width, height = self.width(), self.height()
        if width <= 1:
            return
        track_y = height - 13
        if abs(pos.y() - track_y) > 14:
            return
        left, right = self.THUMB_R + self.PAD, width - self.THUMB_R - self.PAD
        if right <= left:
            return
        ratio = min(max((pos.x() - left) / (right - left), 0.0), 1.0)
        self.set(self.spec.min_value + ratio * (self.spec.max_value - self.spec.min_value), notify=True)

    def _begin_edit(self) -> None:
        if self._editor is not None:
            return
        editor = _InlineEditor(self)
        editor.setText(self._format(self._value))
        editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        editor.setStyleSheet(
            f"background-color: {Color.PANEL_SOFT}; border: none; border-radius: {Radius.PILL}px; "
            f"color: {self.fill_color}; padding: 2px 6px;"
        )
        rect = self._value_rect if self._value_rect.width() > 0 else QRect(self.width() - 74, 0, 70, 20)
        width = max(70, rect.width())
        height = 22
        x = min(max(0, rect.center().x() - width // 2), self.width() - width)
        y = max(0, rect.center().y() - height // 2)
        editor.setGeometry(x, y, width, height)
        self._editor = editor
        editor.editingFinished.connect(lambda: self._commit_edit(editor))
        editor.escapePressed.connect(lambda: self._cancel_edit(editor))
        editor.show()
        editor.setFocus()
        editor.selectAll()
        self.update()

    def _commit_edit(self, editor: _InlineEditor) -> None:
        if self._editor is not editor:
            return
        text = editor.text()
        self._editor = None
        editor.blockSignals(True)
        editor.deleteLater()
        try:
            value = float(text)
        except ValueError:
            value = self._value
        self.set(value, notify=True)

    def _cancel_edit(self, editor: _InlineEditor) -> None:
        if self._editor is not editor:
            return
        self._editor = None
        editor.blockSignals(True)
        editor.deleteLater()
        self.update()
