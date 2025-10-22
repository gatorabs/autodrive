from src.presentation.ui.components.slider import SliderSection, SliderConfig

class ObjectRoiSection(SliderSection):
    """Sliders for defining the ROI of object detection."""
    def __init__(self, master, tk_controls, calibration_data, **kwargs):
        sliders = [
            SliderConfig("Person", "Person", 0, 240),
            SliderConfig("Traffic", "Traffic Sign", 0, 240),
            SliderConfig("PLACA_PARE", "Placa Pare", 0, 240),
            SliderConfig("PLACA_DESVIO", "Placa Desvio", 0, 240),
            SliderConfig("PLACA_LOMBADA", "Placa Lombada", 0, 240),
            SliderConfig("BaseConf", "YOLO Confidence", 0, 10),
            SliderConfig("PeopleRegion", "People Region", 10, 100),
        ]
        super().__init__(master, "ROI de Objetos", tk_controls, calibration_data, sliders, **kwargs)
