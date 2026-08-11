from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QDialog, QGridLayout, QScrollArea, QVBoxLayout, QWidget

from src.application.runtime.state import control_keys as keys
from src.domain.constants.calibration_ranges import (
    CONFIDENCE_RANGE,
    DEVIATION_COUNTER_RANGE,
    STOP_DECELERATION_STEP_RANGE,
    STOP_RAMP_INTERVAL_RANGE,
    TIMESTAMP_RANGE,
)
from src.domain.constants.detour_constants import DEVIATION_COUNTER_CONTROL
from src.presentation.ui.theme.tokens import Space
from src.presentation.ui.widgets.slider_card import SettingsPanel
from src.presentation.ui.widgets.slider_control import SliderSpec

_OPTION_LABELS = [
    keys.WEBVIEW,
    keys.SHOW_ROI,
    keys.SHOW_INFO,
    keys.SEND_LOGS,
    keys.NEW_PID,
    keys.SHOW_LINES,
]


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
                SliderSpec(keys.BASE_CONFIDENCE, "YOLO Confidence", *CONFIDENCE_RANGE),
                SliderSpec(keys.CUSTOM_CONFIDENCE, "Custom YOLO Confidence", *CONFIDENCE_RANGE),
                SliderSpec(keys.SEMAFORO_CONFIDENCE, "Traffic Light YOLO Confidence", *CONFIDENCE_RANGE),
            ],
            controller.tk_controls,
            controller.calibration_data,
            controller.on_slider_value,
        )

        panel.add_section("Stop Ramp")
        panel.add_sliders(
            [
                SliderSpec(keys.STOP_DECELERATION_STEP, "Stop Deceleration Step", *STOP_DECELERATION_STEP_RANGE),
                SliderSpec(keys.STOP_RAMP_INTERVAL, "Stop Ramp Interval (s)", *STOP_RAMP_INTERVAL_RANGE),
                SliderSpec(
                    keys.SEMAFORO_STOP_DECELERATION_STEP,
                    "Traffic Light Stop Deceleration Step",
                    *STOP_DECELERATION_STEP_RANGE,
                ),
                SliderSpec(
                    keys.SEMAFORO_STOP_RAMP_INTERVAL,
                    "Traffic Light Stop Ramp Interval (s)",
                    *STOP_RAMP_INTERVAL_RANGE,
                ),
            ],
            controller.tk_controls,
            controller.calibration_data,
            controller.on_slider_value,
        )

        panel.add_section("General")
        panel.add_sliders(
            [
                SliderSpec(keys.TIMESTAMP, "Timestamp", *TIMESTAMP_RANGE),
                SliderSpec(DEVIATION_COUNTER_CONTROL, "Deviation Counter", *DEVIATION_COUNTER_RANGE),
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
