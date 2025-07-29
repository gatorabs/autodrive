from .slider_section import SliderSection, SliderConfig
import customtkinter as ctk
from queue import Empty

class ManualControls(SliderSection):
    """Sliders to manually control car direction and speed."""

    def __init__(self, master, tk_controls, calibration_data, lane_queue, **kwargs):
        self.lane_queue = lane_queue

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
        if not self.lane_queue.full():
            self.lane_queue.put(lane_data)

    def refresh_from_queue(self) -> None:
        """Update sliders with the latest values from ``lane_queue``."""
        last_lane = None
        while not self.lane_queue.empty():
            try:
                last_lane = self.lane_queue.get_nowait()
            except Empty:
                break

        if last_lane:
            self.lane_queue.put(last_lane)
            speed = last_lane.get("CAR_SPEED_DATA", 0)
            direction = last_lane.get("CAR_DIRECTION_DATA", 0)
            self.set("MANUAL_SPEED", speed)
            self.set("MANUAL_DIRECTION", direction)
