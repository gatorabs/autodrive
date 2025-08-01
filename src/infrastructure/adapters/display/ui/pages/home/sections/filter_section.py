import customtkinter as ctk
from src.infrastructure.adapters.display.ui.components.slider import SliderSection, SliderConfig

class FilterControls(SliderSection):
    """Sliders for basic image filter configuration."""
    def __init__(self, master, tk_controls, calibration_data, **kwargs):
        sliders = [
            SliderConfig("F_Canny", "F_Canny", 0, 255),
            SliderConfig("S_Canny", "S_Canny", 0, 255),
        ]
        super().__init__(master, "Filtros", tk_controls, calibration_data, sliders, **kwargs)
