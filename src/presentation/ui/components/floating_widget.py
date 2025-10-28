from dataclasses import dataclass
from typing import Callable, Dict, Optional

import customtkinter as ctk

from src.infrastructure.data.repository.calibration_repository import (
    load_data,
    refresh_json,
    save_data,
)
from src.infrastructure.constants.ui_constants.file_constants import (
    CALIBRATION_FILE,
    DEFAULTS_FILE,
)
from src.presentation.ui.components.checkbox import CheckboxSection


def _destroy_modal_window(modal: Optional[ctk.CTkToplevel]) -> None:
    if modal is None:
        return
    try:
        modal.grab_release()
        modal.destroy()
    except ctk.TclError:
        pass


def _calculate_modal_geometry(
    parent: ctk.CTkBaseClass,
    button: ctk.CTkBaseClass,
    width: int,
    height: int,
    *,
    x_offset: int = 0,
    y_offset: int = 0,
) -> str:
    parent.update_idletasks()
    parent_x = parent.winfo_rootx()
    parent_y = parent.winfo_rooty()
    button_x = button.winfo_rootx() - parent_x
    button_y = button.winfo_rooty() - parent_y
    modal_x = parent_x + button_x - width + x_offset
    modal_y = parent_y + button_y - height + y_offset
    return f"{width}x{height}+{modal_x}+{modal_y}"


class FloatingWidget(ctk.CTkFrame):
    """Small widget with buttons for saving/restoring defaults and toggles."""

    def __init__(
        self,
        master,
        tk_controls,
        shared_controls,
        checkbox_labels=None,
        **kwargs,
    ):
        super().__init__(master, fg_color="#2b2b2b", **kwargs)
        self.place(relx=1.0, rely=1.0, anchor="se", x=-650, y=-27)

        self.save_data = save_data
        self.load_data = load_data
        self.tk_controls = tk_controls
        self.shared_controls = shared_controls
        self.DEFAULTS_FILE = DEFAULTS_FILE
        self.button_colors = "#2b2b2b"
        self.checkbox_labels = checkbox_labels or [
            "WEBVIEW",
            "SHOW_ROI",
            "SHOW_INFO",
            "SEND_LOGS",
            "NEW_PID",
            "SHOW_LINES",
        ]

        self.save_modal = None
        self.save_modal_open = False
        self.checkbox_modal = None
        self.checkbox_modal_open = False
        self.save_modal_width = 267
        self.save_modal_height = 70
        self.checkbox_modal_width = 460
        self.checkbox_modal_height = 170

        buttons_row = ctk.CTkFrame(self, fg_color="transparent")
        buttons_row.pack(anchor="e")

        self.checkboxes_button = ctk.CTkButton(
            buttons_row,
            text="✅",
            width=40,
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(size=15),
            command=self.toggle_checkbox_modal,
        )
        self.checkboxes_button.pack(side="right")

        self.floating_button = ctk.CTkButton(
            buttons_row,
            text="📂",
            width=40,
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(size=15),
            command=self.toggle_save_modal,
        )
        self.floating_button.pack(side="right", padx=(0, 8))

    def toggle_save_modal(self):
        if self.save_modal_open:
            self._hide_modal("save_modal", "save_modal_open")
            return
        self._hide_modal("checkbox_modal", "checkbox_modal_open")
        self._open_save_modal()

    def toggle_checkbox_modal(self):
        if self.checkbox_modal_open:
            self._hide_modal("checkbox_modal", "checkbox_modal_open")
            return
        self._hide_modal("save_modal", "save_modal_open")
        self._open_checkbox_modal()

    def _hide_modal(self, modal_attr: str, open_flag_attr: str) -> None:
        modal: Optional[ctk.CTkToplevel] = getattr(self, modal_attr, None)
        _destroy_modal_window(modal)
        setattr(self, modal_attr, None)
        setattr(self, open_flag_attr, False)

    def _open_modal(
        self,
        *,
        modal_attr: str,
        open_flag_attr: str,
        button: ctk.CTkBaseClass,
        width: int,
        height: int,
        title: str,
        builder: Callable[[ctk.CTkToplevel], None],
        x_offset: int = 0,
        y_offset: int = 0,
    ) -> None:
        self._hide_modal(modal_attr, open_flag_attr)

        modal = ctk.CTkToplevel(self.master)
        modal.title(title)
        modal.resizable(False, False)
        modal.configure(fg_color="#2b2b2b")
        modal.geometry(
            _calculate_modal_geometry(
                self.master, button, width, height, x_offset=x_offset, y_offset=y_offset
            )
        )
        modal.transient(self.master)
        modal.grab_set()
        modal.protocol(
            "WM_DELETE_WINDOW",
            lambda: self._hide_modal(modal_attr, open_flag_attr),
        )

        setattr(self, modal_attr, modal)
        builder(modal)
        setattr(self, open_flag_attr, True)

    def _open_save_modal(self):
        self._open_modal(
            modal_attr="save_modal",
            open_flag_attr="save_modal_open",
            button=self.floating_button,
            width=self.save_modal_width,
            height=self.save_modal_height,
            title="Opções de Salvar",
            builder=self._build_save_modal,
        )

    def _open_checkbox_modal(self):
        self._open_modal(
            modal_attr="checkbox_modal",
            open_flag_attr="checkbox_modal_open",
            button=self.checkboxes_button,
            width=self.checkbox_modal_width,
            height=self.checkbox_modal_height,
            title="Opções Extras",
            builder=self._build_checkbox_modal,
            x_offset=self.checkboxes_button.winfo_width(),
        )

    def _build_save_modal(self, modal: ctk.CTkToplevel) -> None:
        btn_frame = ctk.CTkFrame(modal, fg_color="#2b2b2b")
        btn_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.button1 = ctk.CTkButton(
            btn_frame,
            text="Salvar Padrão",
            command=self.button_1_action,
            text_color="#1DBF08",
            border_color="#1DBF08",
            border_width=2,
            fg_color=self.button_colors,
            width=125,
            height=40,
        )
        self.button2 = ctk.CTkButton(
            btn_frame,
            text="Restaurar Padrão",
            command=self.button_2_action,
            width=125,
            height=40,
            text_color="#BF081D",
            border_color="#BF081D",
            border_width=2,
            fg_color=self.button_colors,
        )
        self.button1.pack(side="left", padx=(0, 10))
        self.button2.pack(side="left")

    def _build_checkbox_modal(self, modal: ctk.CTkToplevel) -> None:
        content = ctk.CTkFrame(modal, fg_color="#2b2b2b")
        content.pack(fill="both", expand=True, padx=12, pady=15)

        CheckboxSection(
            content,
            labels=self.checkbox_labels,
            tk_controls=self.tk_controls,
            shared_controls=self.shared_controls,
            orientation="grid",
            columns=3,
        ).pack(fill="both", expand=True)

    def button_1_action(self):
        refresh_json(self.tk_controls, self.DEFAULTS_FILE, only_existing_keys=True)
        self._hide_modal("save_modal", "save_modal_open")

    def button_2_action(self):
        self.master.restore_defaults()
        self._hide_modal("save_modal", "save_modal_open")

    def close_modal(self):
        self._hide_modal("save_modal", "save_modal_open")
        self._hide_modal("checkbox_modal", "checkbox_modal_open")


@dataclass(frozen=True)
class SettingsSliderConfig:
    name: str
    label: str
    min_val: float
    max_val: float
    step: float = 1.0


class SettingsFloatingWidget(ctk.CTkFrame):
    """Floating widget dedicated to quick access configuration controls."""

    def __init__(
        self,
        master,
        tk_controls,
        calibration_data,
        *,
        slider_configs=None,
        **kwargs,
    ):
        super().__init__(master, fg_color="#2b2b2b", **kwargs)
        self.place(relx=1.0, rely=1.0, anchor="se", x=-600, y=-27)

        self.tk_controls = tk_controls
        self.calibration_data = calibration_data
        self.slider_configs = slider_configs or [
            SettingsSliderConfig("BaseConf", "YOLO Confidence", 0, 10, 1),
            SettingsSliderConfig("CustomConf", "Custom YOLO Confidence", 0, 10, 1),
            SettingsSliderConfig("Timestamp", "Timestamp", 0, 10, 1),
            SettingsSliderConfig(
                "StopRampInterval",
                "StopRampInterval",
                0.0,
                1.0,
                0.05,
            ),
            SettingsSliderConfig("DeviationCounter", "Deviation Counter", 1, 5, 1),
        ]
        self.slider_controls: Dict[str, dict] = {}

        self.settings_modal = None
        self.settings_modal_open = False

        self._setup_button()

    def _setup_button(self) -> None:
        button_row = ctk.CTkFrame(self, fg_color="transparent")
        button_row.pack(anchor="e")

        self.settings_button = ctk.CTkButton(
            button_row,
            text="⚙️",
            width=40,
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(size=15),
            command=self.toggle_settings_modal,
        )
        self.settings_button.pack(side="right")

    def toggle_settings_modal(self):
        if self.settings_modal_open:
            self._close_settings_modal()
            return
        self._open_settings_modal()

    def _close_settings_modal(self):
        if self.settings_modal_open:
            _destroy_modal_window(self.settings_modal)
            self.settings_modal = None
            self.settings_modal_open = False

    def _open_settings_modal(self):
        _destroy_modal_window(self.settings_modal)

        modal_width = 320
        base_modal_height = 160
        slider_rows = max(1, len(self.slider_configs))
        slider_row_height = 44
        modal_height = max(
            base_modal_height,
            60 + slider_rows * slider_row_height,
        )
        self.settings_modal = ctk.CTkToplevel(self.master)
        self.settings_modal.title("Configurações")
        self.settings_modal.resizable(False, False)
        self.settings_modal.configure(fg_color="#2b2b2b")
        self.settings_modal.geometry(
            _calculate_modal_geometry(
                self.master,
                self.settings_button,
                modal_width,
                modal_height,
                x_offset=self.settings_button.winfo_width(),
            )
        )

        self.settings_modal.transient(self.master)
        self.settings_modal.grab_set()
        self.settings_modal.protocol("WM_DELETE_WINDOW", self._close_settings_modal)

        content = ctk.CTkFrame(self.settings_modal, fg_color="#2b2b2b")
        content.pack(fill="both", expand=True, padx=12, pady=12)

        self.slider_controls = {}
        self._build_sliders(content)
        self.settings_modal_open = True

    def _build_sliders(self, parent: ctk.CTkFrame) -> None:
        for index, config in enumerate(self.slider_configs):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            pady = (0, 8) if index == len(self.slider_configs) - 1 else (0, 4)
            row.pack(fill="x", pady=pady)
            row.columnconfigure(1, weight=1)

            ctk.CTkLabel(row, text=config.label).grid(row=0, column=0, padx=(10, 5))

            num_steps = self._calculate_steps(config)
            slider = ctk.CTkSlider(
                row,
                from_=config.min_val,
                to=config.max_val,
                number_of_steps=num_steps,
                command=lambda value, name=config.name: self._on_slider_change(name, value),
            )

            default_value = self._get_current_value(config)
            slider.set(default_value)
            slider.grid(row=0, column=1, padx=5, sticky="ew")

            entry = ctk.CTkEntry(row, width=55 if config.step < 1 else 45)
            entry.insert(0, self._format_value(default_value, config.step))
            entry.grid(row=0, column=2, padx=(5, 10))
            entry.bind("<Return>", lambda event, name=config.name: self._on_value_submit(event, name))
            entry.bind("<FocusOut>", lambda event, name=config.name: self._on_value_focus_out(event, name))

            self.slider_controls[config.name] = {
                "slider": slider,
                "entry": entry,
                "config": config,
            }

    def _calculate_steps(self, config: SettingsSliderConfig) -> int:
        if config.step <= 0:
            return 1
        span = config.max_val - config.min_val
        if span <= 0:
            return 1
        return max(1, int(round(span / config.step)))

    def _get_current_value(self, config: SettingsSliderConfig) -> float:
        if config.name in self.calibration_data:
            return self.calibration_data[config.name]
        if config.name == "StopRampInterval":
            for legacy_key in ("StopDecelerationInterval", "StopAccelerationInterval"):
                if legacy_key in self.calibration_data:
                    return self.calibration_data[legacy_key]

        if config.name in self.tk_controls:
            return self.tk_controls[config.name]
        if config.name == "StopRampInterval":
            for legacy_key in ("StopDecelerationInterval", "StopAccelerationInterval"):
                if legacy_key in self.tk_controls:
                    return self.tk_controls[legacy_key]

        return config.min_val

    def _format_value(self, value: float, step: float) -> str:
        if step < 1:
            return f"{value:.3f}"
        return str(int(round(value)))

    def _on_slider_change(self, name: str, value: float) -> None:
        slider_info = self.slider_controls.get(name)
        if not slider_info:
            return
        config: SettingsSliderConfig = slider_info["config"]
        stepped_value = self._apply_step(value, config)
        entry: ctk.CTkEntry = slider_info["entry"]
        entry.delete(0, "end")
        entry.insert(0, self._format_value(stepped_value, config.step))
        self._persist_value(name, stepped_value)

    def _on_value_submit(self, event, name: str):
        self._apply_entry_value(name)
        event.widget.winfo_toplevel().focus()

    def _on_value_focus_out(self, _event, name: str):
        self._apply_entry_value(name)

    def _apply_entry_value(self, name: str) -> None:
        slider_info = self.slider_controls.get(name)
        if not slider_info:
            return

        entry: ctk.CTkEntry = slider_info["entry"]
        slider: ctk.CTkSlider = slider_info["slider"]
        config: SettingsSliderConfig = slider_info["config"]

        try:
            value = float(entry.get())
        except ValueError:
            value = slider.get()

        value = max(min(value, config.max_val), config.min_val)
        stepped_value = self._apply_step(value, config)
        slider.set(stepped_value)
        entry.delete(0, "end")
        entry.insert(0, self._format_value(stepped_value, config.step))
        self._persist_value(name, stepped_value)

    def _apply_step(self, value: float, config: SettingsSliderConfig) -> float:
        if config.step <= 0:
            return value
        stepped = round((value - config.min_val) / config.step) * config.step + config.min_val
        if config.step >= 1:
            return int(round(stepped))
        return stepped

    def _persist_value(self, name: str, value: float) -> None:
        updates = {name: value}
        if name == "StopRampInterval":
            for legacy_key in ("StopDecelerationInterval", "StopAccelerationInterval"):
                self.tk_controls.pop(legacy_key, None)
                self.calibration_data.pop(legacy_key, None)

        for key, stored_value in updates.items():
            self.tk_controls[key] = stored_value
            self.calibration_data[key] = stored_value

        refresh_json(updates, CALIBRATION_FILE)

    def close_modal(self):
        self._close_settings_modal()
