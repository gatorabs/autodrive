from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QToolButton, QVBoxLayout, QWidget

from src.presentation.ui.theme.icons import get_icon
from src.presentation.ui.theme.tokens import Color, Size


class NavRail(QWidget):
    ITEMS = (
        ("Home", "home", "Home"),
        ("Manual", "manual", "Manual"),
        ("Task Manager", "activity", "Tasks"),
    )

    def __init__(
        self,
        on_select: Callable[[str], None],
        on_settings: Callable[[], None],
        on_defaults: Callable[[], None],
        on_options: Callable[[], None],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setObjectName("NavRail")
        self.setFixedWidth(Size.SIDEBAR_WIDTH)
        self.on_select = on_select
        self.buttons: dict[str, QToolButton] = {}
        self.indicators: dict[str, QFrame] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 20, 0, 18)
        layout.setSpacing(6)

        nav_layout = QVBoxLayout()
        nav_layout.setSpacing(6)
        nav_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        for key, glyph, label in self.ITEMS:
            row = QHBoxLayout()
            row.setSpacing(2)
            indicator = QFrame(self)
            indicator.setFixedSize(3, 32)
            self.indicators[key] = indicator

            button = QToolButton(self)
            button.setObjectName("NavButton")
            button.setText(label)
            button.setIcon(get_icon(glyph, 20, Color.MUTED))
            button.setIconSize(QSize(20, 20))
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            button.setFixedSize(Size.SIDEBAR_WIDTH - 20, 56)
            button.clicked.connect(lambda _checked=False, k=key: self.on_select(k))
            self.buttons[key] = button

            row.addWidget(indicator)
            row.addWidget(button)
            nav_layout.addLayout(row)
        layout.addLayout(nav_layout)
        layout.addStretch(1)

        footer = QVBoxLayout()
        footer.setSpacing(4)
        footer.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        for glyph, command in (("settings", on_settings), ("defaults", on_defaults), ("options", on_options)):
            button = QToolButton(self)
            button.setObjectName("IconButton")
            button.setIcon(get_icon(glyph, 18, Color.MUTED))
            button.setIconSize(QSize(18, 18))
            button.setFixedSize(36, 36)
            button.clicked.connect(command)
            footer.addWidget(button)
        layout.addLayout(footer)

        self.set_active("Home")

    def set_active(self, name: str) -> None:
        glyphs = {key: glyph for key, glyph, _ in self.ITEMS}
        for key, button in self.buttons.items():
            active = key == name
            button.setIcon(get_icon(glyphs[key], 20, Color.TEXT if active else Color.MUTED))
            button.setProperty("active", "true" if active else "false")
            style = button.style()
            style.unpolish(button)
            style.polish(button)
            self.indicators[key].setStyleSheet(
                f"background-color: {Color.PRIMARY if active else 'transparent'}; border-radius: 2px;"
            )
