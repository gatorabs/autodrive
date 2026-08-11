from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from src.presentation.ui.controller import AppController
from src.presentation.ui.theme.stylesheet import build_qss


def launch_application(manager) -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(build_qss())

    controller = AppController(manager)
    controller.start()

    app.exec()
