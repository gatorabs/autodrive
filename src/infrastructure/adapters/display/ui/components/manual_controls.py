from .slider_section import SliderSection, SliderConfig
import customtkinter as ctk

class ManualControls(SliderSection):
    """Sliders to manually control car direction and speed."""

    def __init__(self, master, tk_controls, calibration_data, car_data,
                 on_direction_change=None, **kwargs):
        self.car_data = car_data
        self._on_direction_change_cb = on_direction_change
        sliders = [
            SliderConfig("MANUAL_DIRECTION", "Direção", 0, 180),
            SliderConfig("MANUAL_SPEED", "Velocidade", 0, 255),
        ]

        super().__init__(master, "Controle Manual", tk_controls, calibration_data, sliders, **kwargs)

    def _on_slider_change(self, name: str, value: float, step: float) -> None:
        super()._on_slider_change(name, value, step)
        lane_data = {
            "CAR_SPEED_DATA": self.tk_controls.get("MANUAL_SPEED", 0),
            "CAR_DIRECTION_DATA": self.tk_controls.get("MANUAL_DIRECTION", 0),
        }
        if name == "MANUAL_DIRECTION" and self._on_direction_change_cb:
            self._on_direction_change_cb(lane_data["CAR_DIRECTION_DATA"])
        self.car_data = lane_data
        print(lane_data)
