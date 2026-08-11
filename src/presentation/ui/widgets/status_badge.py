from __future__ import annotations

from PySide6.QtWidgets import QLabel, QWidget


class StatusBadge(QLabel):
    def __init__(self, text: str, tone: str = "muted", parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("StatusBadge")
        self.set(text, tone)

    def set(self, text: str, tone: str = "muted") -> None:
        self.setText(text)
        self.setProperty("tone", tone)
        style = self.style()
        style.unpolish(self)
        style.polish(self)
