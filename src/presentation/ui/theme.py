"""Visual tokens for the rebuilt desktop interface."""

from __future__ import annotations

import customtkinter as ctk
from PIL import Image, ImageDraw


class Theme:
    BG = "#0b0d12"
    PANEL = "#141821"
    PANEL_ALT = "#1a1f2b"
    PANEL_SOFT = "#212736"
    SIDEBAR = "#10131b"
    INPUT = "#0f1420"
    BORDER = "#262d3d"
    BORDER_HOVER = "#3a4356"
    TEXT = "#f5f7fb"
    MUTED = "#9aa5bb"
    SUBTLE = "#5b667e"

    PRIMARY = "#3b82f6"
    PRIMARY_HOVER = "#2563eb"
    PRIMARY_SOFT = "#182a4a"

    SECONDARY = "#22d3ee"
    SECONDARY_HOVER = "#0891b2"
    SECONDARY_SOFT = "#0f2f37"

    SUCCESS = "#34d399"
    SUCCESS_SOFT = "#123527"
    WARNING = "#fbbf24"
    WARNING_SOFT = "#3a2c0f"
    DANGER = "#f87171"
    DANGER_SOFT = "#3a1620"

    RADIUS_SM = 9
    RADIUS = 12
    RADIUS_LG = 16
    RADIUS_PILL = 999

    SPACE_XS = 4
    SPACE_SM = 8
    SPACE_MD = 12
    SPACE_LG = 20
    SPACE_XL = 32

    SIDEBAR_WIDTH = 84
    MIN_WIDTH = 1024
    MIN_HEIGHT = 680
    VIDEO_MIN_HEIGHT = 205
    ROW_GAP = 8


_FONT_CACHE: dict[tuple[int, str | None], ctk.CTkFont] = {}


def font(size: int, weight: str | None = None) -> ctk.CTkFont:
    key = (size, weight)
    cached = _FONT_CACHE.get(key)
    if cached is None:
        cached = ctk.CTkFont(size=size, weight=weight)
        _FONT_CACHE[key] = cached
    return cached


def font_display() -> ctk.CTkFont:
    return font(26, "bold")


def font_heading() -> ctk.CTkFont:
    return font(16, "bold")


def font_body() -> ctk.CTkFont:
    return font(13)


def font_label() -> ctk.CTkFont:
    return font(12, "bold")


def font_caption() -> ctk.CTkFont:
    return font(11)


def card_style() -> dict:
    return {
        "fg_color": Theme.PANEL,
        "border_color": Theme.BORDER,
        "border_width": 1,
        "corner_radius": Theme.RADIUS,
    }


def accent_card_style(color: str = Theme.PRIMARY) -> dict:
    return {
        "fg_color": Theme.PANEL,
        "border_color": color,
        "border_width": 1,
        "corner_radius": Theme.RADIUS,
    }


def button_style(primary: bool = False) -> dict:
    return {
        "height": 34,
        "corner_radius": Theme.RADIUS_SM,
        "fg_color": Theme.PRIMARY if primary else Theme.PANEL_SOFT,
        "hover_color": Theme.PRIMARY_HOVER if primary else Theme.BORDER_HOVER,
        "text_color": Theme.TEXT,
    }


def nav_button_style(active: bool = False) -> dict:
    return {
        "width": Theme.SIDEBAR_WIDTH - 20,
        "height": 56,
        "corner_radius": Theme.RADIUS_SM,
        "fg_color": Theme.PANEL_SOFT if active else "transparent",
        "hover_color": Theme.PANEL_ALT,
        "text_color": Theme.TEXT if active else Theme.MUTED,
    }


def icon_button_style(active: bool = False) -> dict:
    return {
        "width": 36,
        "height": 36,
        "corner_radius": Theme.RADIUS_SM,
        "fg_color": Theme.PRIMARY if active else "transparent",
        "hover_color": Theme.PANEL_SOFT,
        "text_color": Theme.TEXT,
    }


def input_style() -> dict:
    return {
        "fg_color": Theme.INPUT,
        "border_color": Theme.BORDER_HOVER,
        "button_color": Theme.PANEL_SOFT,
        "button_hover_color": Theme.BORDER_HOVER,
    }


def chip_entry_style(accent: str = Theme.PRIMARY) -> dict:
    return {
        "fg_color": Theme.PANEL_SOFT,
        "border_width": 0,
        "corner_radius": Theme.RADIUS_PILL,
        "text_color": accent,
        "justify": "center",
    }


def badge_style(tone: str = "info") -> dict:
    tones = {
        "info": (Theme.PRIMARY_SOFT, Theme.PRIMARY),
        "accent": (Theme.SECONDARY_SOFT, Theme.SECONDARY),
        "success": (Theme.SUCCESS_SOFT, Theme.SUCCESS),
        "warning": (Theme.WARNING_SOFT, Theme.WARNING),
        "danger": (Theme.DANGER_SOFT, Theme.DANGER),
        "muted": (Theme.PANEL_SOFT, Theme.MUTED),
    }
    bg, fg = tones.get(tone, tones["info"])
    return {"fg_color": bg, "text_color": fg}


_ICON_CACHE: dict[tuple[str, int, str], "ctk.CTkImage"] = {}
_SUPERSAMPLE = 4


def icon(name: str, size: int = 18, color: str | None = None) -> "ctk.CTkImage":
    color = color or Theme.TEXT
    key = (name, size, color)
    cached = _ICON_CACHE.get(key)
    if cached is not None:
        return cached

    canvas = size * _SUPERSAMPLE
    image = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    stroke = max(2, canvas // 11)
    _ICON_DRAWERS.get(name, _draw_dot)(draw, canvas, stroke, color)
    image = image.resize((size, size), Image.Resampling.LANCZOS)

    ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=(size, size))
    _ICON_CACHE[key] = ctk_image
    return ctk_image


def _pad(canvas: int, ratio: float = 0.18) -> tuple[int, int]:
    inset = int(canvas * ratio)
    return inset, canvas - inset


def _draw_home(draw: ImageDraw.ImageDraw, canvas: int, stroke: int, color: str) -> None:
    lo, hi = _pad(canvas, 0.14)
    mid_x = canvas / 2
    roof_y = lo
    eave_y = lo + (hi - lo) * 0.38
    draw.line([(mid_x, roof_y), (lo, eave_y)], fill=color, width=stroke, joint="curve")
    draw.line([(mid_x, roof_y), (hi, eave_y)], fill=color, width=stroke, joint="curve")
    draw.line([(lo, eave_y), (lo, hi)], fill=color, width=stroke)
    draw.line([(hi, eave_y), (hi, hi)], fill=color, width=stroke)
    draw.line([(lo, hi), (hi, hi)], fill=color, width=stroke)
    door_w = (hi - lo) * 0.26
    draw.rectangle(
        [mid_x - door_w / 2, hi - (hi - eave_y) * 0.62, mid_x + door_w / 2, hi],
        outline=color,
        width=max(2, stroke - 1),
    )


def _draw_manual(draw: ImageDraw.ImageDraw, canvas: int, stroke: int, color: str) -> None:
    lo, hi = _pad(canvas, 0.12)
    cx = cy = canvas / 2
    radius = (hi - lo) / 2
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], outline=color, width=stroke)
    hub = radius * 0.32
    draw.ellipse([cx - hub, cy - hub, cx + hub, cy + hub], outline=color, width=max(2, stroke - 1))
    draw.line([(cx, cy - hub), (cx, cy - radius)], fill=color, width=stroke)
    for angle_deg in (150, 30):
        import math

        rad = math.radians(angle_deg)
        x1 = cx + hub * math.cos(rad)
        y1 = cy - hub * math.sin(rad)
        x2 = cx + radius * math.cos(rad)
        y2 = cy - radius * math.sin(rad)
        draw.line([(x1, y1), (x2, y2)], fill=color, width=stroke)


def _draw_activity(draw: ImageDraw.ImageDraw, canvas: int, stroke: int, color: str) -> None:
    lo, hi = _pad(canvas, 0.18)
    base = hi
    bar_w = (hi - lo) / 4.6
    heights = (0.45, 0.85, 0.62, 1.0)
    for index, ratio in enumerate(heights):
        x0 = lo + index * bar_w * 1.35
        x1 = x0 + bar_w
        y0 = base - (hi - lo) * ratio
        draw.rounded_rectangle([x0, y0, x1, base], radius=bar_w * 0.3, outline=color, width=max(2, stroke - 1))


def _draw_settings(draw: ImageDraw.ImageDraw, canvas: int, stroke: int, color: str) -> None:
    import math

    cx = cy = canvas / 2
    radius = canvas * 0.28
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], outline=color, width=stroke)
    hole = radius * 0.42
    draw.ellipse([cx - hole, cy - hole, cx + hole, cy + hole], outline=color, width=max(2, stroke - 1))
    tooth_len = canvas * 0.14
    for tooth in range(8):
        angle = math.radians(tooth * 45)
        x1 = cx + radius * math.cos(angle)
        y1 = cy + radius * math.sin(angle)
        x2 = cx + (radius + tooth_len) * math.cos(angle)
        y2 = cy + (radius + tooth_len) * math.sin(angle)
        draw.line([(x1, y1), (x2, y2)], fill=color, width=stroke)


def _draw_defaults(draw: ImageDraw.ImageDraw, canvas: int, stroke: int, color: str) -> None:
    lo, hi = _pad(canvas, 0.2)
    cx = canvas / 2
    draw.rounded_rectangle([lo, lo, hi, hi], radius=(hi - lo) * 0.16, outline=color, width=stroke)
    top = lo + (hi - lo) * 0.22
    draw.line([(cx, top), (cx, hi - (hi - lo) * 0.22)], fill=color, width=stroke)
    arrow = (hi - lo) * 0.16
    mid_y = hi - (hi - lo) * 0.22
    draw.line([(cx - arrow, mid_y - arrow), (cx, mid_y)], fill=color, width=stroke)
    draw.line([(cx + arrow, mid_y - arrow), (cx, mid_y)], fill=color, width=stroke)


def _draw_options(draw: ImageDraw.ImageDraw, canvas: int, stroke: int, color: str) -> None:
    lo, hi = _pad(canvas, 0.18)
    rows = (0.0, 0.5, 1.0)
    knobs = (0.32, 0.68, 0.45)
    for row, knob in zip(rows, knobs):
        y = lo + (hi - lo) * row
        draw.line([(lo, y), (hi, y)], fill=color, width=max(2, stroke - 1))
        knob_x = lo + (hi - lo) * knob
        r = stroke * 1.1
        draw.ellipse([knob_x - r, y - r, knob_x + r, y + r], fill=color)


def _draw_dot(draw: ImageDraw.ImageDraw, canvas: int, stroke: int, color: str) -> None:
    lo, hi = _pad(canvas, 0.3)
    draw.ellipse([lo, lo, hi, hi], fill=color)


def _draw_alert(draw: ImageDraw.ImageDraw, canvas: int, stroke: int, color: str) -> None:
    lo, hi = _pad(canvas, 0.22)
    cx = canvas / 2
    bar_bottom = lo + (hi - lo) * 0.55
    draw.line([(cx, lo), (cx, bar_bottom)], fill=color, width=stroke)
    dot_r = stroke * 0.9
    dot_y = hi - dot_r
    draw.ellipse([cx - dot_r, dot_y - dot_r, cx + dot_r, dot_y + dot_r], fill=color)


_ICON_DRAWERS = {
    "home": _draw_home,
    "manual": _draw_manual,
    "activity": _draw_activity,
    "settings": _draw_settings,
    "defaults": _draw_defaults,
    "options": _draw_options,
    "dot": _draw_dot,
    "alert": _draw_alert,
}
