from .slider_section import SliderSection, SliderConfig
import customtkinter as ctk
from queue import Empty

class ManualControls(SliderSection):
    """Sliders to manually control car direction and speed."""

    def __init__(self, master, tk_controls, calibration_data, shared_controls, **kwargs):
        self.shared_controls = shared_controls
        self.car_data = shared_controls.get("CAR_INFO", {})
        sliders = [
            SliderConfig("MANUAL_DIRECTION", "Dire\u00e7\u00e3o", 0, 180),
            SliderConfig("MANUAL_SPEED", "Velocidade", 0, 255),
        ]

        super().__init__(master, "Controle Manual", tk_controls, calibration_data, sliders, **kwargs)

    def _on_slider_change(self, name: str, value: float, step: float) -> None:
        super()._on_slider_change(name, value, step)
        lane_data = {
            "CAR_SPEED_DATA": self.tk_controls.get("MANUAL_SPEED", 0),
            "CAR_DIRECTION_DATA": self.tk_controls.get("MANUAL_DIRECTION", 0),
        }
        self.shared_controls["CAR_INFO"] = lane_data
        self.car_data = lane_data