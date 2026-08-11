from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from src.presentation.ui.theme.icons import icon_pixmap
from src.presentation.ui.theme.tokens import Color, Space


class Card(QFrame):
    def __init__(
        self,
        title: str | None = None,
        *,
        accent: str | None = None,
        icon_name: str | None = None,
        bordered: bool = True,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setObjectName("Card")
        if accent:
            self.setProperty("accent", accent)
        self.setProperty("bordered", "true" if bordered else "false")

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self.header: QWidget | None = None
        self._header_layout: QHBoxLayout | None = None
        if title:
            self.header = QWidget(self)
            self._header_layout = QHBoxLayout(self.header)
            self._header_layout.setContentsMargins(Space.MD + 2, Space.MD - 1, Space.MD + 2, Space.SM - 2)
            self._header_layout.setSpacing(Space.SM)
            if icon_name:
                badge = QLabel(self.header)
                badge.setFixedSize(28, 28)
                badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
                badge_bg, badge_fg = Color.tone(accent or "primary")
                badge.setStyleSheet(f"background-color: {badge_bg}; border-radius: 8px;")
                badge.setPixmap(icon_pixmap(icon_name, 15, badge_fg))
                self._header_layout.addWidget(badge)
            title_label = QLabel(title, self.header)
            title_label.setObjectName("CardTitle")
            self._header_layout.addWidget(title_label, 1)
            self._layout.addWidget(self.header)

        self.body = QWidget(self)
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(Space.MD + 2, 0, Space.MD + 2, Space.MD + 2)
        self.body_layout.setSpacing(Space.XS)
        self._layout.addWidget(self.body, 1)

    def set_accessory(self, widget: QWidget) -> None:
        if self._header_layout is None:
            return
        self._header_layout.addWidget(widget, 0, Qt.AlignmentFlag.AlignRight)
