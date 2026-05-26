from dataclasses import dataclass
from typing import Any
import customtkinter as ctk

from src.infrastructure.data.repository.calibration_repository import default_settings_store
from src.infrastructure.constants.ui_constants.file_constants import CALIBRATION_FILE

@dataclass
class SliderConfig:
    """Configuration for a slider used in :class:`SliderSection`."""
    name: str
    label: str
    min_val: float
    max_val: float
    step: float = 1.0

class SliderSection(ctk.CTkFrame):
    """Generic section that holds multiple sliders."""

    def __init__(
        self,
        master,
        title: str,
        tk_controls: dict,
        calibration_data: dict,
        sliders_config: list[SliderConfig],
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self.tk_controls = tk_controls
        self.calibration_data = calibration_data
        self.settings_store = default_settings_store
        self._no_persist = {"MANUAL_DIRECTION", "MANUAL_SPEED", "Side"}

        ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0, 10))

        self.sliders: dict[str, dict[str, Any]] = {}

        for config in sliders_config:
            if not isinstance(config, SliderConfig):
                raise TypeError(
                    f"Esperado SliderConfig em sliders_config, mas recebeu: {type(config)}"
                )

            name = config.name
            label = config.label
            min_val = config.min_val
            max_val = config.max_val
            step = config.step

            default = self.calibration_data.get(name, self.tk_controls.get(name, min_val))
            slider, value_entry = self.add_slider(
                self,
                label_text=label,
                name=name,
                from_=min_val,
                to=max_val,
                default=default,
                step=step
            )
            self.sliders[name] = {
                "slider": slider,
                "label": value_entry,
                "step": step,
                "from": min_val,
                "to": max_val,
            }

    def add_slider(
        self,
        parent: ctk.CTkFrame,
        label_text: str,
        name: str,
        from_: float,
        to: float,
        default: float,
        step: float = 1.0,
    ) -> tuple[ctk.CTkSlider, ctk.CTkEntry]:
        row = ctk.CTkFrame(parent)
        row.pack(fill="x", padx=20, pady=2)
        row.columnconfigure(1, weight=1)

        ctk.CTkLabel(row, text=label_text).grid(row=0, column=0, padx=(10, 5))

        num_steps = int(round((to - from_) / step))

        slider = ctk.CTkSlider(
            row,
            from_=from_,
            to=to,
            number_of_steps=num_steps,
            command=lambda value, n=name, s=step, l=label_text: self._on_slider_change(n, value, s)
        )
        slider.set(default)
        slider.grid(row=0, column=1, padx=5, sticky="ew")

        if step < 1:
            text = f"{default:.3f}"
        else:
            text = str(int(default))
        value_entry = ctk.CTkEntry(row, width=45)
        value_entry.insert(0, text)
        value_entry.grid(row=0, column=2, padx=(5, 10))
        value_entry.bind(
            "<Return>",
            lambda event, n=name: self._on_value_submit(event, n),
        )
        value_entry.bind(
            "<FocusOut>",
            lambda event, n=name: self._on_value_edit(n, event),
        )

        return slider, value_entry

    def _on_slider_change(self, name: str, value: float, step: float) -> None:
        stepped_value = round(value / step) * step

        entry = self.sliders[name]["label"]
        if step < 1:
            display = f"{stepped_value:.3f}"
        else:
            stepped_value = int(stepped_value)
            display = str(stepped_value)
        entry.delete(0, "end")
        entry.insert(0, display)

        self.tk_controls[name] = stepped_value
        if name not in self._no_persist:
            self.settings_store.update({name: stepped_value}, CALIBRATION_FILE)

    def get(self, name: str) -> float:
        slider_data = self.sliders[name]
        step = slider_data.get("step", 1.0)
        value = slider_data["slider"].get()
        if step < 1:
            return round(value / step) * step
        return int(value)

    def set(self, name: str, value: float) -> None:
        slider_data = self.sliders[name]
        step = slider_data.get("step", 1.0)

        stepped_value = round(value / step) * step
        slider_data["slider"].set(stepped_value)
        self._on_slider_change(name, stepped_value, step)

    def _on_value_edit(self, name: str, event: Any | None = None) -> None:
        slider_data = self.sliders[name]
        entry: ctk.CTkEntry = slider_data["label"]
        step = slider_data.get("step", 1.0)
        from_ = slider_data.get("from", 0.0)
        to = slider_data.get("to", 0.0)
        try:
            value = float(entry.get())
        except ValueError:
            value = slider_data["slider"].get()
        value = max(min(value, to), from_)
        slider_data["slider"].set(value)
        self._on_slider_change(name, value, step)
        if event is not None:
            event.widget.winfo_toplevel().focus()

    def _on_value_submit(self, event: Any, name: str) -> None:
        """Validate the typed value and move focus away from the entry."""
        self._on_value_edit(name, event)
