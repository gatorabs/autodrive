from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget

from src.presentation.ui.theme.tokens import Color, Type


class StatusBadge(QFrame):
    """A pill-shaped status indicator: a colored dot plus an uppercase label."""

    def __init__(self, text: str, tone: str = "muted", parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("StatusBadge")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 12, 0)
        layout.setSpacing(6)
        self.setFixedHeight(24)

        self._dot = QLabel(self)
        self._dot.setFixedSize(6, 6)
        layout.addWidget(self._dot, 0, Qt.AlignmentFlag.AlignVCenter)

        self._text = QLabel(self)
        font = QFont(Type.FAMILY, Type.CAPTION, QFont.Weight.DemiBold)
        font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 105)
        self._text.setFont(font)
        layout.addWidget(self._text, 0, Qt.AlignmentFlag.AlignVCenter)

        self.set(text, tone)

    def set(self, text: str, tone: str = "muted") -> None:
        self._text.setText(text.upper())
        self.setProperty("tone", tone)
        style = self.style()
        style.unpolish(self)
        style.polish(self)

        _, fg = Color.tone(tone)
        self._dot.setStyleSheet(f"background-color: {fg}; border-radius: 3px;")
        self._text.setStyleSheet(f"color: {fg}; background: transparent;")
