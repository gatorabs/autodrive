"""Minimal QPainter horizontal bar chart, replacing the old matplotlib chart."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

from src.presentation.ui.theme.tokens import Color, Type


class BarChartWidget(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._labels: list[str] = []
        self._values: list[float] = []
        self._unit = ""

    def set_data(self, labels: list[str], values: list[float], unit: str) -> None:
        self._labels = labels
        self._values = values
        self._unit = unit
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        painter.fillRect(rect, QColor(Color.PANEL))

        if not self._values:
            painter.setPen(QColor(Color.MUTED))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "No Python processes found")
            painter.end()
            return

        margin_left, margin_right, margin_top, margin_bottom = 60, 56, 8, 20
        chart_rect = QRectF(
            margin_left, margin_top, rect.width() - margin_left - margin_right, rect.height() - margin_top - margin_bottom
        )
        max_value = max(self._values) or 1

        grid_pen = QPen(QColor(Color.BORDER))
        grid_pen.setStyle(Qt.PenStyle.DashLine)
        grid_pen.setWidthF(0.6)
        painter.setPen(grid_pen)
        for i in range(5):
            x = chart_rect.left() + chart_rect.width() * i / 4
            painter.drawLine(QPointF(x, chart_rect.top()), QPointF(x, chart_rect.bottom()))

        font = QFont(Type.FAMILY, Type.CAPTION)
        painter.setFont(font)

        count = len(self._values)
        gap = 6
        bar_height = max(4.0, min(22.0, (chart_rect.height() - gap * (count - 1)) / count)) if count else 0.0

        y = chart_rect.top()
        for label, value in zip(self._labels, self._values):
            bar_w = chart_rect.width() * (value / max_value)
            bar_rect = QRectF(chart_rect.left(), y, bar_w, bar_height)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(Color.PRIMARY))
            painter.drawRoundedRect(bar_rect, 3, 3)

            painter.setPen(QColor(Color.TEXT))
            label_rect = QRectF(0, y, margin_left - 8, bar_height)
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, label)

            painter.setPen(QColor(Color.MUTED))
            value_rect = QRectF(chart_rect.left() + bar_w + 4, y, margin_right - 4, bar_height)
            painter.drawText(value_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, f"{value:.1f}")

            y += bar_height + gap

        painter.setPen(QColor(Color.MUTED))
        unit_rect = QRectF(chart_rect.left(), rect.height() - margin_bottom, chart_rect.width(), margin_bottom)
        painter.drawText(unit_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self._unit)
        painter.end()
