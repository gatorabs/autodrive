"""Vector icon set drawn with QPainter, replacing the old PIL-based icons."""

from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap

from src.presentation.ui.theme.tokens import Color

_PIXMAP_CACHE: dict[tuple[str, int, str], QPixmap] = {}


def _inset(size: int, ratio: float) -> tuple[float, float]:
    pad = size * ratio
    return pad, size - pad


def _draw_home(p: QPainter, size: float) -> None:
    lo, hi = _inset(size, 0.16)
    mid = size / 2
    eave = lo + (hi - lo) * 0.38
    p.drawLine(QPointF(mid, lo), QPointF(lo, eave))
    p.drawLine(QPointF(mid, lo), QPointF(hi, eave))
    p.drawLine(QPointF(lo, eave), QPointF(lo, hi))
    p.drawLine(QPointF(hi, eave), QPointF(hi, hi))
    p.drawLine(QPointF(lo, hi), QPointF(hi, hi))
    door_w = (hi - lo) * 0.26
    p.drawRect(QRectF(mid - door_w / 2, hi - (hi - eave) * 0.62, door_w, (hi - eave) * 0.62))


def _draw_manual(p: QPainter, size: float) -> None:
    lo, hi = _inset(size, 0.12)
    cx = cy = size / 2
    radius = (hi - lo) / 2
    p.drawEllipse(QPointF(cx, cy), radius, radius)
    hub = radius * 0.32
    p.drawEllipse(QPointF(cx, cy), hub, hub)
    p.drawLine(QPointF(cx, cy - hub), QPointF(cx, cy - radius))
    for angle_deg in (150, 30):
        rad = math.radians(angle_deg)
        x1, y1 = cx + hub * math.cos(rad), cy - hub * math.sin(rad)
        x2, y2 = cx + radius * math.cos(rad), cy - radius * math.sin(rad)
        p.drawLine(QPointF(x1, y1), QPointF(x2, y2))


def _draw_activity(p: QPainter, size: float) -> None:
    lo, hi = _inset(size, 0.18)
    base = hi
    bar_w = (hi - lo) / 4.6
    heights = (0.45, 0.85, 0.62, 1.0)
    for index, ratio in enumerate(heights):
        x0 = lo + index * bar_w * 1.35
        y0 = base - (hi - lo) * ratio
        p.drawRoundedRect(QRectF(x0, y0, bar_w, base - y0), bar_w * 0.3, bar_w * 0.3)


def _draw_settings(p: QPainter, size: float) -> None:
    cx = cy = size / 2
    radius = size * 0.28
    p.drawEllipse(QPointF(cx, cy), radius, radius)
    hole = radius * 0.42
    p.drawEllipse(QPointF(cx, cy), hole, hole)
    tooth_len = size * 0.14
    for tooth in range(8):
        angle = math.radians(tooth * 45)
        x1, y1 = cx + radius * math.cos(angle), cy + radius * math.sin(angle)
        x2, y2 = cx + (radius + tooth_len) * math.cos(angle), cy + (radius + tooth_len) * math.sin(angle)
        p.drawLine(QPointF(x1, y1), QPointF(x2, y2))


def _draw_defaults(p: QPainter, size: float) -> None:
    lo, hi = _inset(size, 0.2)
    cx = size / 2
    p.drawRoundedRect(QRectF(lo, lo, hi - lo, hi - lo), (hi - lo) * 0.16, (hi - lo) * 0.16)
    top = lo + (hi - lo) * 0.22
    mid_y = hi - (hi - lo) * 0.22
    p.drawLine(QPointF(cx, top), QPointF(cx, mid_y))
    arrow = (hi - lo) * 0.16
    p.drawLine(QPointF(cx - arrow, mid_y - arrow), QPointF(cx, mid_y))
    p.drawLine(QPointF(cx + arrow, mid_y - arrow), QPointF(cx, mid_y))


def _draw_options(p: QPainter, size: float) -> None:
    lo, hi = _inset(size, 0.18)
    rows = (0.0, 0.5, 1.0)
    knobs = (0.32, 0.68, 0.45)
    pen = p.pen()
    for row, knob in zip(rows, knobs):
        y = lo + (hi - lo) * row
        p.drawLine(QPointF(lo, y), QPointF(hi, y))
        knob_x = lo + (hi - lo) * knob
        r = pen.widthF() * 1.4
        p.setBrush(pen.color())
        p.drawEllipse(QPointF(knob_x, y), r, r)


def _draw_camera(p: QPainter, size: float) -> None:
    lo, hi = _inset(size, 0.18)
    body_top = lo + (hi - lo) * 0.2
    cx = (lo + hi) / 2
    p.drawRoundedRect(QRectF(lo, body_top, hi - lo, hi - body_top), (hi - lo) * 0.14, (hi - lo) * 0.14)
    bump_w = (hi - lo) * 0.32
    p.drawRoundedRect(
        QRectF(cx - bump_w / 2, body_top - (hi - lo) * 0.16, bump_w, (hi - lo) * 0.16),
        (hi - lo) * 0.05,
        (hi - lo) * 0.05,
    )
    lens_r = (hi - lo) * 0.22
    cy = body_top + (hi - body_top) * 0.55
    p.drawEllipse(QPointF(cx, cy), lens_r, lens_r)
    dot_r = lens_r * 0.32
    pen = p.pen()
    p.setBrush(pen.color())
    p.drawEllipse(QPointF(cx, cy), dot_r, dot_r)


def _draw_target(p: QPainter, size: float) -> None:
    cx = cy = size / 2
    r_outer = size * 0.32
    r_mid = size * 0.19
    p.drawEllipse(QPointF(cx, cy), r_outer, r_outer)
    p.drawEllipse(QPointF(cx, cy), r_mid, r_mid)
    dot_r = size * 0.07
    pen = p.pen()
    p.setBrush(pen.color())
    p.drawEllipse(QPointF(cx, cy), dot_r, dot_r)


def _draw_alert(p: QPainter, size: float) -> None:
    lo, hi = _inset(size, 0.22)
    cx = size / 2
    bar_bottom = lo + (hi - lo) * 0.55
    p.drawLine(QPointF(cx, lo), QPointF(cx, bar_bottom))
    pen = p.pen()
    dot_r = pen.widthF() * 0.9
    dot_y = hi - dot_r
    p.setBrush(pen.color())
    p.drawEllipse(QPointF(cx, dot_y), dot_r, dot_r)


def _draw_dot(p: QPainter, size: float) -> None:
    lo, hi = _inset(size, 0.3)
    pen = p.pen()
    p.setBrush(pen.color())
    p.drawEllipse(QRectF(lo, lo, hi - lo, hi - lo))


_DRAWERS = {
    "home": _draw_home,
    "manual": _draw_manual,
    "activity": _draw_activity,
    "settings": _draw_settings,
    "defaults": _draw_defaults,
    "options": _draw_options,
    "camera": _draw_camera,
    "target": _draw_target,
    "alert": _draw_alert,
    "dot": _draw_dot,
}


def icon_pixmap(name: str, size: int = 18, color: str | None = None) -> QPixmap:
    color = color or Color.TEXT
    key = (name, size, color)
    cached = _PIXMAP_CACHE.get(key)
    if cached is not None:
        return cached

    ratio = 4
    canvas = size * ratio
    pixmap = QPixmap(canvas, canvas)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    pen = QPen(QColor(color))
    pen.setWidthF(max(2.0, canvas / 11))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    _DRAWERS.get(name, _draw_dot)(painter, canvas)
    painter.end()

    pixmap = pixmap.scaled(
        size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
    )
    _PIXMAP_CACHE[key] = pixmap
    return pixmap


def get_icon(name: str, size: int = 18, color: str | None = None) -> QIcon:
    return QIcon(icon_pixmap(name, size, color))
