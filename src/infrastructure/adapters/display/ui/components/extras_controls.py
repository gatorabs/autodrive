from src.infrastructure.constants.video_constants import FRAME_HEIGHT
from .slider_section import SliderSection, SliderConfig
from .checkbox_section import CheckboxSection

class ExtrasControls(SliderSection):
    """Additional sliders and checkboxes for extra options."""
    def __init__(self, master, tk_controls, calibration_data, shared_controls, **kwargs):
        sliders = [
            SliderConfig("Lines", "Lines", 0, FRAME_HEIGHT),
            SliderConfig("Distance", "Distance", 0, 270),
            SliderConfig("Speed", "Speed", 0, 255),
            SliderConfig("Side", "Side", 1, 2),
        ]

        super().__init__(master, "Extras", tk_controls, calibration_data, sliders, **kwargs)
        self.checkbox_section = CheckboxSection(
            self,
            labels=["WEBVIEW", "SHOW_ROI", "SHOW_INFO", "SEND_LOGS", "NEW_PID"],
            tk_controls=self.tk_controls,
            shared_controls=shared_controls,
            orientation="grid",
            columns=3
        )
        self.checkbox_section.pack(fill="x", padx=2, pady=(33, 0))
