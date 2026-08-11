from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from src.presentation.ui.theme.icons import icon_pixmap
from src.presentation.ui.theme.tokens import Color, Space


class ConfirmDialog(QDialog):
    def __init__(self, title: str, message: str, tone: str = "warning", parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedWidth(320)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Space.LG + 4, Space.LG + 4, Space.LG + 4, Space.LG)
        layout.setSpacing(Space.SM)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        bg, fg = Color.tone(tone)
        icon_wrap = QLabel(self)
        icon_wrap.setFixedSize(48, 48)
        icon_wrap.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_wrap.setStyleSheet(f"background-color: {bg}; border-radius: 24px;")
        icon_wrap.setPixmap(icon_pixmap("alert", 20, fg))
        layout.addWidget(icon_wrap, 0, Qt.AlignmentFlag.AlignHCenter)

        title_label = QLabel(title, self)
        title_label.setStyleSheet("font-weight: 600; font-size: 15px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        message_label = QLabel(message, self)
        message_label.setStyleSheet(f"color: {Color.MUTED};")
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(message_label)

        buttons = QHBoxLayout()
        buttons.setSpacing(Space.SM)
        cancel_btn = QPushButton("Cancel", self)
        cancel_btn.clicked.connect(self.reject)
        confirm_btn = QPushButton("Confirm", self)
        confirm_btn.setProperty("variant", "primary")
        confirm_btn.clicked.connect(self.accept)
        buttons.addWidget(cancel_btn)
        buttons.addWidget(confirm_btn)
        layout.addLayout(buttons)

    @classmethod
    def ask(cls, parent: QWidget | None, title: str, message: str, tone: str = "warning") -> bool:
        dialog = cls(title, message, tone, parent)
        return dialog.exec() == QDialog.DialogCode.Accepted
