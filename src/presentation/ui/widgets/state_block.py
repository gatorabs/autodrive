from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from src.presentation.ui.theme.tokens import Color, Space

_TONE_COLOR = {
    "info": Color.TEXT,
    "success": Color.SUCCESS,
    "warning": Color.WARNING,
    "error": Color.DANGER,
}


class StateBlock(QFrame):
    def __init__(self, title: str, message: str, tone: str = "info", parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("StateBlock")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Space.MD + 2, Space.MD, Space.MD + 2, Space.MD)
        layout.setSpacing(2)

        title_label = QLabel(title, self)
        title_label.setStyleSheet(f"font-weight: 600; font-size: 15px; color: {_TONE_COLOR.get(tone, Color.TEXT)};")
        layout.addWidget(title_label)

        message_label = QLabel(message, self)
        message_label.setStyleSheet(f"color: {Color.MUTED};")
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
