from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QDialog, QGridLayout, QScrollArea, QVBoxLayout, QWidget

from src.presentation.ui.theme.tokens import Space
from src.presentation.ui.widgets.slider_card import SettingsPanel
from src.presentation.ui.widgets.slider_control import SliderSpec

_OPTION_LABELS = ["WEBVIEW", "SHOW_ROI", "SHOW_INFO", "SEND_LOGS", "NEW_PID", "SHOW_LINES"]


class SettingsDialog(QDialog):
    def __init__(self, controller, parent: QWidget | None = None):
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("Settings")
        self.setMinimumWidth(440)
        self.resize(460, 640)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Space.MD, Space.MD, Space.MD, Space.MD)

        panel = SettingsPanel(None)

        panel.add_section("Detection Confidence")
        panel.add_sliders(
            [
                SliderSpec("BaseConf", "YOLO Confidence", 0, 10),
                SliderSpec("CustomConf", "Custom YOLO Confidence", 0, 10),
                SliderSpec("SemaforoConf", "Traffic Light YOLO Confidence", 0, 10),
            ],
            controller.tk_controls,
            controller.calibration_data,
            controller.on_slider_value,
        )

        panel.add_section("Stop Ramp")
        panel.add_sliders(
            [
                SliderSpec("StopDecelerationStep", "Stop Deceleration Step", 1, 100),
                SliderSpec("StopRampInterval", "Stop Ramp Interval (s)", 0.0, 1.0, 0.05),
                SliderSpec("SEMAFORO_StopDecelerationStep", "Traffic Light Stop Deceleration Step", 1, 100),
                SliderSpec("SEMAFORO_StopRampInterval", "Traffic Light Stop Ramp Interval (s)", 0.0, 1.0, 0.05),
            ],
            controller.tk_controls,
            controller.calibration_data,
            controller.on_slider_value,
        )

        panel.add_section("General")
        panel.add_sliders(
            [
                SliderSpec("Timestamp", "Timestamp", 0, 10),
                SliderSpec("DeviationCounter", "Deviation Counter", 0, 5),
            ],
            controller.tk_controls,
            controller.calibration_data,
            controller.on_slider_value,
        )

        panel.add_section("Runtime Options")
        panel.add_content(self._build_options_content)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setWidget(panel)
        layout.addWidget(scroll)

    def _build_options_content(self, frame: QWidget) -> None:
        grid = QGridLayout()
        for index, label in enumerate(_OPTION_LABELS):
            checkbox = QCheckBox(label, frame)
            checkbox.setChecked(bool(self.controller.tk_controls.get(label, False)))
            checkbox.toggled.connect(lambda checked, key=label: self.controller.set_option(key, checked))
            grid.addWidget(checkbox, index // 2, index % 2)
        frame.layout().addLayout(grid)
