from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QStackedWidget, QVBoxLayout, QWidget

from src.presentation.ui.dialogs.defaults_dialog import DefaultsDialog
from src.presentation.ui.dialogs.options_dialog import OptionsDialog
from src.presentation.ui.dialogs.settings_dialog import SettingsDialog
from src.presentation.ui.theme.tokens import Size, Space
from src.presentation.ui.views.home_view import HomeView
from src.presentation.ui.views.manual_view import ManualView
from src.presentation.ui.views.task_manager_view import TaskManagerView
from src.presentation.ui.widgets.confirm_dialog import ConfirmDialog
from src.presentation.ui.widgets.nav_rail import NavRail
from src.presentation.ui.widgets.status_badge import StatusBadge


class MainWindow(QMainWindow):
    def __init__(self, controller, parent: QWidget | None = None):
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("Autonomous Team")
        self.setMinimumSize(Size.MIN_WIDTH, Size.MIN_HEIGHT)

        central = QWidget(self)
        central.setObjectName("Root")
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.nav = NavRail(self.select, self.open_settings, self.open_defaults, self.open_options)
        root_layout.addWidget(self.nav)

        right = QWidget(central)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        root_layout.addWidget(right, 1)

        topbar = QWidget(right)
        topbar.setObjectName("TopBar")
        topbar.setFixedHeight(Size.TOPBAR_HEIGHT)
        topbar_layout = QHBoxLayout(topbar)
        topbar_layout.setContentsMargins(Space.LG, 0, Space.LG, 0)
        title_label = QLabel("Autonomous Team", topbar)
        title_label.setObjectName("AppTitle")
        topbar_layout.addWidget(title_label)
        topbar_layout.addStretch(1)
        self.mode_badge = StatusBadge("Auto", "primary")
        self.cuda_badge = StatusBadge("CUDA -", "muted")
        self.safety_badge = StatusBadge("Nominal", "success")
        for badge in (self.mode_badge, self.cuda_badge, self.safety_badge):
            topbar_layout.addWidget(badge)
        right_layout.addWidget(topbar)

        self.stack = QStackedWidget(right)
        right_layout.addWidget(self.stack, 1)

        status_row = QHBoxLayout()
        status_row.setContentsMargins(Space.LG, 4, Space.LG, Space.MD)
        self.status = StatusBadge("Ready", "muted")
        status_row.addWidget(self.status)
        status_row.addStretch(1)
        right_layout.addLayout(status_row)

        self.home_view = HomeView(controller)
        self.manual_view = ManualView(controller)
        self.task_manager_view = TaskManagerView()
        self.views = {"Home": self.home_view, "Manual": self.manual_view, "Task Manager": self.task_manager_view}
        for view in self.views.values():
            self.stack.addWidget(view)

        self.current_view_name: str | None = None
        self._activate("Manual" if controller.shared_controls.manual_mode else "Home")

    def select(self, name: str) -> None:
        if name == "Manual" and not self.controller.shared_controls.manual_mode:
            if not ConfirmDialog.ask(
                self, "Enable manual mode", "The vehicle will switch to manual driving control.", "warning"
            ):
                return
            self.controller.set_manual_mode(True)
        elif name == "Home" and self.controller.shared_controls.manual_mode:
            if not ConfirmDialog.ask(
                self, "Disable manual mode", "The vehicle will return to autonomous control.", "primary"
            ):
                return
            self.controller.set_manual_mode(False)
        self._activate(name)

    def _activate(self, name: str) -> None:
        if self.current_view_name == name:
            return
        if self.current_view_name == "Task Manager":
            self.task_manager_view.set_active(False)
        self.current_view_name = name
        self.stack.setCurrentWidget(self.views[name])
        self.nav.set_active(name)
        if name == "Task Manager":
            self.task_manager_view.set_active(True)

    def sync_state(self, manual_mode: bool, safe_stop: bool, object_safe_stop: bool) -> None:
        if manual_mode:
            self.mode_badge.set("Manual", "warning")
        else:
            self.mode_badge.set("Auto", "primary")
        if safe_stop or object_safe_stop:
            self.safety_badge.set("Safe-stop", "danger")
        else:
            self.safety_badge.set("Nominal", "success")

    def set_cuda_status(self, available: bool, device_name: str) -> None:
        if available:
            self.cuda_badge.set(device_name or "CUDA", "success")
        else:
            self.cuda_badge.set("CPU only", "muted")

    def show_status(self, message: str, tone: str = "info") -> None:
        tone_map = {"success": "success", "warning": "warning", "error": "danger"}.get(tone, "muted")
        self.status.set(message, tone_map)

    def open_settings(self) -> None:
        SettingsDialog(self.controller, self).exec()

    def open_defaults(self) -> None:
        DefaultsDialog(self.controller, self).exec()

    def open_options(self) -> None:
        OptionsDialog(self.controller, self).exec()

    def closeEvent(self, event) -> None:
        self.controller.cleanup()
        super().closeEvent(event)
