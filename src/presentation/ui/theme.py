"""Visual tokens for the rebuilt desktop interface."""

from __future__ import annotations

import customtkinter as ctk


class Theme:
    BG = "#0f1115"
    PANEL = "#171a21"
    PANEL_ALT = "#1f2430"
    PANEL_SOFT = "#252b38"
    INPUT = "#0f172a"
    BORDER = "#2d3442"
    BORDER_HOVER = "#3b4558"
    TEXT = "#f8fafc"
    MUTED = "#a8b3c7"
    SUBTLE = "#64748b"
    PRIMARY = "#3b82f6"
    PRIMARY_HOVER = "#2563eb"
    SUCCESS = "#22c55e"
    WARNING = "#f59e0b"
    DANGER = "#ef4444"
    RADIUS = 12
    RADIUS_SM = 9
    MIN_WIDTH = 960
    MIN_HEIGHT = 640
    VIDEO_MIN_HEIGHT = 205
    ROW_GAP = 8


def font(size: int, weight: str | None = None) -> ctk.CTkFont:
    return ctk.CTkFont(size=size, weight=weight)


def card_style() -> dict:
    return {
        "fg_color": Theme.PANEL,
        "border_color": Theme.BORDER,
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


def input_style() -> dict:
    return {
        "fg_color": Theme.INPUT,
        "border_color": Theme.BORDER_HOVER,
        "button_color": Theme.PANEL_SOFT,
        "button_hover_color": Theme.BORDER_HOVER,
    }
