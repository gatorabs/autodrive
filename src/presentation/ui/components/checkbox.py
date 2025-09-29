import customtkinter as ctk

from src.infrastructure.data.repository.calibration_repository import refresh_json
from src.infrastructure.constants.ui_constants.file_constants import CALIBRATION_FILE, DEFAULT_UI_PATH
from src.infrastructure.logging.logger import Logger

logger = Logger("CheckboxSection")

class CheckboxSection(ctk.CTkFrame):
    """Group of checkboxes that persist their state."""

    def __init__(self, master, labels, tk_controls, shared_controls, orientation="horizontal", columns=2, **kwargs):
        super().__init__(master, **kwargs)
        self.labels = labels
        self.tk_controls = tk_controls
        self.columns = columns
        self.vars = {}
        self.shared_controls = shared_controls
        self.refresh_json = refresh_json

        if orientation == "grid":
            self._create_grid()
        elif orientation == "horizontal":
            self._create_horizontal()
        elif orientation == "vertical":
            self._create_vertical()

    def _create_grid(self):
        for index, label in enumerate(self.labels):
            row = index // self.columns
            col = index % self.columns
            self._create_checkbox(label, row=row, column=col)

    def _create_horizontal(self):
        for label in self.labels:
            self._create_checkbox(label).pack(side="left", padx=10)

    def _create_vertical(self):
        for label in self.labels:
            self._create_checkbox(label).pack(anchor="w", pady=2)

    def _create_checkbox(self, label, row=None, column=None):
        initial_value = self.tk_controls.get(label, False)
        var = ctk.BooleanVar(value=initial_value)
        checkbox = ctk.CTkCheckBox(self, text=label, variable=var, command=self._save_state)
        self.vars[label] = var

        if row is not None and column is not None:
            checkbox.grid(row=row, column=column, padx=6, pady=5, sticky="w")

        return checkbox

    def _save_state(self):
        updates = {}
        for label, var in self.vars.items():
            value = var.get()
            self.tk_controls[label] = value
            if label in ("WEBVIEW", "NEW_PID"):
                self._save_to_default(label, value)
            else:
                updates[label] = value
        if updates:
            refresh_json(updates, path=CALIBRATION_FILE)

    def _save_to_default(self, key: str, value: bool):
        try:
            self.refresh_json({key: value}, path=DEFAULT_UI_PATH)
            self.shared_controls[key] = value

        except Exception as e:
            logger.error(f"Erro ao salvar em {DEFAULT_UI_PATH}: {e}")

    def get_states(self):
        return {label: var.get() for label, var in self.vars.items()}
