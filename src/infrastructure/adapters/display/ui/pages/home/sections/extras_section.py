from src.infrastructure.constants.video_constants import FRAME_HEIGHT
from src.infrastructure.adapters.display.ui.components.slider import SliderSection, SliderConfig
from src.infrastructure.adapters.display.ui.components.checkbox import CheckboxSection

class ExtrasControls(SliderSection):
    """Additional sliders and checkboxes for extra options."""
    def __init__(self, master, tk_controls, calibration_data, shared_controls, **kwargs):
        self.shared_controls = shared_controls

        sliders = [
            SliderConfig("Lines", "Lines", 0, FRAME_HEIGHT),
            SliderConfig("Distance", "Distance", 0, 270),
            SliderConfig("Speed", "Speed", 0, 255),
            SliderConfig("Side", "Side", 1, 2),
        ]

        super().__init__(master, "Extras", tk_controls, calibration_data, sliders, **kwargs)
        self.checkbox_section = CheckboxSection(
            self,
            labels=["WEBVIEW", "SHOW_ROI", "SHOW_INFO", "SEND_LOGS", "NEW_PID", "SHOW_LINES"],
            tk_controls=self.tk_controls,
            shared_controls=shared_controls,
            orientation="grid",
            columns=3
        )
        self.checkbox_section.pack(fill="x", padx=2, pady=(33, 0))

        self._update_lines_slider()

    def _update_lines_slider(self):
        max_height = self.shared_controls.get("MAX_HEIGHT")
        if isinstance(max_height, (int, float)) and max_height > 0:
            slider_data = self.sliders.get("Lines")
            if slider_data:
                slider = slider_data["slider"]
                step = slider_data.get("step", 1.0)
                from_ = slider_data.get("from", 0)
                current_to = slider_data.get("to")
                if max_height != current_to:
                    num_steps = max(1, int(round((max_height - from_) / step)))
                    slider.configure(to=max_height, number_of_steps=num_steps)
                    slider_data["to"] = max_height
                    if self.tk_controls.get("Lines", 0) > max_height:
                        self.set("Lines", max_height)
        self.after(200, self._update_lines_slider)
