from src.presentation.ui.components.slider import SliderConfig, SliderSection


class ObjectRoiSection(SliderSection):
    """Sliders for defining the ROI of object detection."""

    def __init__(self, master, tk_controls, calibration_data, **kwargs):
        sliders = [
            SliderConfig("Person", "Pessoa", 0, 240),
            SliderConfig("SEMAFORO", "Semaforo", 0, 240),
            SliderConfig("PeopleRegion", "Regiao Pessoa", 10, 100),
            SliderConfig("PLACA_PARE", "Placa Pare", 0, 240),
            SliderConfig("PLACA_DESVIO", "Placa Desvio", 0, 240),
            SliderConfig("PLACA_LOMBADA", "Placa Lombada", 0, 240),
        ]
        super().__init__(
            master,
            "Deteccao de Objetos",
            tk_controls,
            calibration_data,
            sliders,
            **kwargs,
        )
