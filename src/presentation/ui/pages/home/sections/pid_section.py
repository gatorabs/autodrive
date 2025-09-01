from src.presentation.ui.components.slider import SliderSection, SliderConfig

class PIDSection(SliderSection):
    """PID gain sliders."""
    def __init__(self, master, tk_controls, calibration_data, **kwargs):
        sliders_config = [
            SliderConfig("KP", "KP", 0.0, 5.0, 0.01),
            SliderConfig("KI", "KI", 0.0, 10.0, 0.001),
            SliderConfig("KD", "KD", 0.0, 10.0, 0.001),
        ]
        super().__init__(
            master=master,
            title="PID",
            tk_controls=tk_controls,
            calibration_data=calibration_data,
            sliders_config=sliders_config,
            height=120,
            **kwargs
        )
