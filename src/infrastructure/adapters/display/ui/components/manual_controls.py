from .slider_section import SliderSection, SliderConfig
import customtkinter as ctk
from queue import Empty


class ManualControls(SliderSection):
    """Sliders to manually control car direction and speed."""

    def __init__(self, master, tk_controls, calibration_data, lane_queue, **kwargs):
        self.lane_queue = lane_queue

        last_lane = None
        while not lane_queue.empty():
            try:
                last_lane = lane_queue.get_nowait()
            except Empty:
                break

        if last_lane:
            lane_queue.put(last_lane)
            tk_controls["MANUAL_SPEED"] = last_lane.get("CAR_SPEED_DATA", 0)
            tk_controls["MANUAL_DIRECTION"] = last_lane.get("CAR_DIRECTION_DATA", 0)

        sliders = [
            SliderConfig("MANUAL_DIRECTION", "Direção", 0, 180),
            SliderConfig("MANUAL_SPEED", "Velocidade", 0, 255),
        ]

        width = kwargs.pop("width", None)
        super().__init__(master, "Controle Manual", tk_controls, calibration_data, sliders, width=width, **kwargs)
        self.grid_propagate(False)

    def _on_slider_change(self, name: str, value: float, step: float) -> None:
        super()._on_slider_change(name, value, step)
        lane_data = {
            "CAR_SPEED_DATA": self.tk_controls.get("MANUAL_SPEED", 0),
            "CAR_DIRECTION_DATA": self.tk_controls.get("MANUAL_DIRECTION", 0),
        }
        if not self.lane_queue.full():
            self.lane_queue.put(lane_data)

