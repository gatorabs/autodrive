from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QDialog, QGridLayout, QVBoxLayout, QWidget

from src.presentation.ui.theme.tokens import Space
from src.presentation.ui.widgets.card import Card

_LABELS = ["WEBVIEW", "SHOW_ROI", "SHOW_INFO", "SEND_LOGS", "NEW_PID", "SHOW_LINES"]


class OptionsDialog(QDialog):
    def __init__(self, controller, parent: QWidget | None = None):
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("Options")
        self.setMinimumWidth(320)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Space.MD, Space.MD, Space.MD, Space.MD)
        card = Card("Options")
        layout.addWidget(card)

        grid = QGridLayout()
        for index, label in enumerate(_LABELS):
            checkbox = QCheckBox(label, card)
            checkbox.setChecked(bool(controller.tk_controls.get(label, False)))
            checkbox.toggled.connect(lambda checked, key=label: controller.set_option(key, checked))
            grid.addWidget(checkbox, index // 2, index % 2)
        card.body_layout.addLayout(grid)
