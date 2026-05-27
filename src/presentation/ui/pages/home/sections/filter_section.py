import customtkinter as ctk
from src.presentation.ui.components.slider import SliderSection, SliderConfig

class FilterControls(SliderSection):
    """Sliders for basic image filter configuration."""
    def __init__(self, master, tk_controls, calibration_data, **kwargs):
        sliders = [
            SliderConfig("F_Canny", "Canny baixo", 0, 255),
            SliderConfig("S_Canny", "Canny alto", 0, 255),
        ]
        super().__init__(master, "Filtros de Imagem", tk_controls, calibration_data, sliders, **kwargs)
