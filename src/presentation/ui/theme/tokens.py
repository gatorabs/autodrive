"""Design tokens for the PySide6 desktop UI: the single source of truth for
colors, spacing, radii, typography, and fixed sizes used across the app."""

from __future__ import annotations


class Color:
    BG = "#0a0e15"
    PANEL = "#121822"
    PANEL_ALT = "#171f2b"
    PANEL_SOFT = "#1e2836"
    SIDEBAR = "#0d1219"
    INPUT_BG = "#0c1119"
    BORDER = "#232c3b"
    BORDER_STRONG = "#3a465c"

    TEXT = "#eef2f9"
    MUTED = "#8b97ad"
    SUBTLE = "#516079"

    PRIMARY = "#2dd4bf"
    PRIMARY_HOVER = "#14b8a6"
    PRIMARY_SOFT = "#10302c"

    SECONDARY = "#a78bfa"
    SECONDARY_HOVER = "#8b5cf6"
    SECONDARY_SOFT = "#241f3d"

    SUCCESS = "#4ade80"
    SUCCESS_SOFT = "#132a1d"
    WARNING = "#fbbf24"
    WARNING_SOFT = "#332a0d"
    DANGER = "#f87171"
    DANGER_SOFT = "#3a1a20"

    @classmethod
    def tone(cls, tone: str) -> tuple[str, str]:
        """Return (background, foreground) for a semantic tone name."""
        tones = {
            "primary": (cls.PRIMARY_SOFT, cls.PRIMARY),
            "secondary": (cls.SECONDARY_SOFT, cls.SECONDARY),
            "success": (cls.SUCCESS_SOFT, cls.SUCCESS),
            "warning": (cls.WARNING_SOFT, cls.WARNING),
            "danger": (cls.DANGER_SOFT, cls.DANGER),
            "muted": (cls.PANEL_SOFT, cls.MUTED),
        }
        return tones.get(tone, tones["muted"])


class Space:
    XS = 4
    SM = 8
    MD = 12
    LG = 20
    XL = 32


class Radius:
    SM = 6
    MD = 10
    LG = 14
    PILL = 999


class Type:
    FAMILY = "Segoe UI"
    MONO_FAMILY = "Consolas"

    DISPLAY = 24
    HEADING = 15
    BODY = 12
    LABEL = 11
    CAPTION = 10


class Size:
    SIDEBAR_WIDTH = 88
    MIN_WIDTH = 1200
    MIN_HEIGHT = 760
    VIDEO_MIN_HEIGHT = 200
    ROW_GAP = 10
    TOPBAR_HEIGHT = 60
