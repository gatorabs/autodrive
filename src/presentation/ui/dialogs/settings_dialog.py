from __future__ import annotations

from PySide6.QtWidgets import QDialog, QVBoxLayout, QWidget

from src.presentation.ui.theme.tokens import Space
from src.presentation.ui.widgets.slider_card import SliderCard
from src.presentation.ui.widgets.slider_control import SliderSpec

_SPECS = [
    SliderSpec("BaseConf", "YOLO Confidence", 0, 10),
    SliderSpec("CustomConf", "Custom YOLO Confidence", 0, 10),
    SliderSpec("SemaforoConf", "Traffic Light YOLO Confidence", 0, 10),
    SliderSpec("Timestamp", "Timestamp", 0, 10),
    SliderSpec("StopDecelerationStep", "Stop Deceleration Step", 1, 100),
    SliderSpec("StopRampInterval", "Stop Ramp Interval (s)", 0.0, 1.0, 0.05),
    SliderSpec("SEMAFORO_StopDecelerationStep", "Traffic Light Stop Deceleration Step", 1, 100),
    SliderSpec("SEMAFORO_StopRampInterval", "Traffic Light Stop Ramp Interval (s)", 0.0, 1.0, 0.05),
    SliderSpec("DeviationCounter", "Deviation Counter", 0, 5),
]


class SettingsDialog(QDialog):
    def __init__(self, controller, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Space.MD, Space.MD, Space.MD, Space.MD)
        card = SliderCard(
            "Settings",
            _SPECS,
            controller.tk_controls,
            controller.calibration_data,
            controller.on_slider_value,
            icon_name="settings",
        )
        layout.addWidget(card)
