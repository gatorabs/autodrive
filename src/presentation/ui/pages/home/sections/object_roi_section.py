from src.presentation.ui.components.slider import SliderSection, SliderConfig

class ObjectRoiSection(SliderSection):
    """Sliders for defining the ROI of object detection."""
    def __init__(self, master, tk_controls, calibration_data, **kwargs):
        sliders = [
            SliderConfig("Person", "Person", 0, 240),
            SliderConfig("Traffic", "Traffic Sign", 0, 240),
            SliderConfig("Ex1", "Extra Object", 0, 10),
            SliderConfig("Ex2", "Extra Object 2", 0, 10),
        ]
        super().__init__(master, "ROI de Objetos", tk_controls, calibration_data, sliders, **kwargs)
