from __future__ import annotations

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget

from src.presentation.ui.theme.icons import icon_pixmap
from src.presentation.ui.theme.tokens import Color, Space, Type
from src.presentation.ui.widgets.card import Card
from src.presentation.ui.widgets.state_block import StateBlock

_PROGRESS_MESSAGES = {
    25: "Loading settings",
    50: "Detecting cameras",
    75: "Checking serial ports",
    100: "Finalizing runtime",
}


class BootWorker(QObject):
    progress = Signal(int, str)
    finished = Signal(dict)
    failed = Signal(str)

    def __init__(self, initializer):
        super().__init__()
        self.initializer = initializer

    def run(self) -> None:
        def progress_callback(value: int) -> None:
            self.progress.emit(value, _PROGRESS_MESSAGES.get(value, "Initializing"))

        try:
            flags = self.initializer.prepare_initial_flags(progress_callback=progress_callback)
        except Exception as exc:  # noqa: BLE001 - boot must surface startup failures.
            self.failed.emit(str(exc))
            return
        self.finished.emit(flags)


class BootWindow(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Autonomous Team")
        self.resize(560, 420)
        self.setMinimumSize(480, 340)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(Space.XL, Space.XL, Space.XL, Space.XL)
        shell = Card()
        outer.addWidget(shell)

        layout = shell.body_layout
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.setContentsMargins(Space.LG, Space.XL, Space.LG, Space.LG)
        layout.setSpacing(Space.SM)

        badge = QLabel(self)
        badge.setFixedSize(64, 64)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(f"background-color: {Color.PRIMARY_SOFT}; border-radius: 32px;")
        badge.setPixmap(icon_pixmap("manual", 34, Color.PRIMARY))
        layout.addWidget(badge, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacing(Space.SM)

        title = QLabel("Autonomous Team", self)
        title.setStyleSheet(f"font-size: {Type.DISPLAY}px; font-weight: 700;")
        layout.addWidget(title, 0, Qt.AlignmentFlag.AlignHCenter)

        subtitle = QLabel("Starting dashboard, processes, and devices", self)
        subtitle.setStyleSheet(f"color: {Color.MUTED};")
        layout.addWidget(subtitle, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacing(Space.LG)

        self.progress = QProgressBar(self)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFixedHeight(8)
        layout.addWidget(self.progress)

        self.step_label = QLabel("Preparing...", self)
        self.step_label.setStyleSheet(f"color: {Color.MUTED};")
        layout.addWidget(self.step_label, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacing(Space.LG)

        self.state_slot = QVBoxLayout()
        layout.addLayout(self.state_slot)

    def set_progress(self, value: float, message: str) -> None:
        self.progress.setValue(int(max(0, min(value, 100))))
        self.step_label.setText(message)

    def show_error(self, message: str) -> None:
        self._clear_state()
        self.state_slot.addWidget(StateBlock("Startup failed", message, "error"))

    def show_cuda_status(self, available: bool, device_name: str, message: str) -> None:
        self._clear_state()
        title = f"CUDA ready: {device_name}" if available else "CUDA recommended"
        tone = "success" if available else "warning"
        self.state_slot.addWidget(StateBlock(title, message, tone))

    def _clear_state(self) -> None:
        while self.state_slot.count():
            item = self.state_slot.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
