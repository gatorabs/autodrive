from __future__ import annotations

from PySide6.QtWidgets import QDialog, QPushButton, QVBoxLayout, QWidget

from src.presentation.ui.theme.tokens import Space
from src.presentation.ui.widgets.card import Card


class DefaultsDialog(QDialog):
    def __init__(self, controller, parent: QWidget | None = None):
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("Defaults")
        self.setMinimumWidth(280)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Space.MD, Space.MD, Space.MD, Space.MD)
        card = Card("Defaults")
        layout.addWidget(card)

        save_btn = QPushButton("Save default", card)
        save_btn.setProperty("variant", "primary")
        save_btn.clicked.connect(self._save)
        card.body_layout.addWidget(save_btn)

        restore_btn = QPushButton("Restore default", card)
        restore_btn.clicked.connect(self._restore)
        card.body_layout.addWidget(restore_btn)

    def _save(self) -> None:
        self.controller.save_defaults()
        self.accept()

    def _restore(self) -> None:
        self.controller.restore_defaults()
        self.accept()
