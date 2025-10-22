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
            self._close_save_modal()
            return
        self._close_checkbox_modal()
        self._open_save_modal()

    def toggle_checkbox_modal(self):
        if self.checkbox_modal_open:
            self._close_checkbox_modal()
            return
        self._close_save_modal()
        self._open_checkbox_modal()

    def _close_save_modal(self):
        if self.save_modal_open and self.save_modal:
            try:
                self.save_modal.grab_release()
                self.save_modal.destroy()
            except ctk.TclError:
                pass
            finally:
                self.save_modal = None
                self.save_modal_open = False

    def _close_checkbox_modal(self):
        if self.checkbox_modal_open and self.checkbox_modal:
            try:
                self.checkbox_modal.grab_release()
                self.checkbox_modal.destroy()
            except ctk.TclError:
                pass
            finally:
                self.checkbox_modal = None
                self.checkbox_modal_open = False

    def _open_save_modal(self):
        if self.save_modal:
            try:
                self.save_modal.destroy()
            except ctk.TclError:
                pass

        self.save_modal = ctk.CTkToplevel(self.master)
        self.save_modal.title("Opções de Salvar")
        self.save_modal.resizable(False, False)
        self.save_modal.configure(fg_color="#2b2b2b")

        self.master.update_idletasks()
        parent_x = self.master.winfo_rootx()
        parent_y = self.master.winfo_rooty()
        button_x = self.floating_button.winfo_rootx() - parent_x
        button_y = self.floating_button.winfo_rooty() - parent_y
        modal_x = parent_x + button_x - self.save_modal_width
        modal_y = parent_y + button_y - self.save_modal_height
        geometry = f"{self.save_modal_width}x{self.save_modal_height}+{modal_x}+{modal_y}"
        self.save_modal.geometry(geometry)

        self.save_modal.transient(self.master)
        self.save_modal.grab_set()
        self.save_modal.protocol("WM_DELETE_WINDOW", self._close_save_modal)

        btn_frame = ctk.CTkFrame(self.save_modal, fg_color="#2b2b2b")
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

        self.save_modal_open = True

    def _open_checkbox_modal(self):
        if self.checkbox_modal:
            try:
                self.checkbox_modal.destroy()
            except ctk.TclError:
                pass

        self.checkbox_modal = ctk.CTkToplevel(self.master)
        self.checkbox_modal.title("Opções Extras")
        self.checkbox_modal.resizable(False, False)
        self.checkbox_modal.configure(fg_color="#2b2b2b")

        self.master.update_idletasks()
        parent_x = self.master.winfo_rootx()
        parent_y = self.master.winfo_rooty()
        button_x = self.checkboxes_button.winfo_rootx() - parent_x
        button_y = self.checkboxes_button.winfo_rooty() - parent_y
        modal_x = (
            parent_x
            + button_x
            - self.checkbox_modal_width
            + self.checkboxes_button.winfo_width()
        )
        modal_y = parent_y + button_y - self.checkbox_modal_height
        geometry = f"{self.checkbox_modal_width}x{self.checkbox_modal_height}+{modal_x}+{modal_y}"
        self.checkbox_modal.geometry(geometry)

        self.checkbox_modal.transient(self.master)
        self.checkbox_modal.grab_set()
        self.checkbox_modal.protocol("WM_DELETE_WINDOW", self._close_checkbox_modal)

        content = ctk.CTkFrame(self.checkbox_modal, fg_color="#2b2b2b")
        content.pack(fill="both", expand=True, padx=12, pady=15)

        CheckboxSection(
            content,
            labels=self.checkbox_labels,
            tk_controls=self.tk_controls,
            shared_controls=self.shared_controls,
            orientation="grid",
            columns=3,
        ).pack(fill="both", expand=True)

        self.checkbox_modal_open = True

    def button_1_action(self):
        refresh_json(self.tk_controls, self.DEFAULTS_FILE, only_existing_keys=True)
        self._close_save_modal()

    def button_2_action(self):
        self.master.restore_defaults()
        self._close_save_modal()

    def close_modal(self):
        self._close_save_modal()
        self._close_checkbox_modal()


class SettingsFloatingWidget(ctk.CTkFrame):
    """Floating widget dedicated to quick access configuration controls."""

    def __init__(
        self,
        master,
        tk_controls,
        calibration_data,
        *,
        slider_name="BaseConf",
        slider_label="YOLO Confidence",
        slider_min=0,
        slider_max=10,
        slider_step=1,
        **kwargs,
    ):
        super().__init__(master, fg_color="#2b2b2b", **kwargs)
        self.place(relx=1.0, rely=1.0, anchor="se", x=-590, y=-27)

        self.tk_controls = tk_controls
        self.calibration_data = calibration_data
        self.slider_name = slider_name
        self.slider_label = slider_label
        self.slider_min = slider_min
        self.slider_max = slider_max
        self.slider_step = slider_step

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
        if self.settings_modal_open and self.settings_modal:
            try:
                self.settings_modal.grab_release()
                self.settings_modal.destroy()
            except ctk.TclError:
                pass
            finally:
                self.settings_modal = None
                self.settings_modal_open = False

    def _open_settings_modal(self):
        if self.settings_modal:
            try:
                self.settings_modal.destroy()
            except ctk.TclError:
                pass

        self.settings_modal = ctk.CTkToplevel(self.master)
        self.settings_modal.title("Configurações")
        self.settings_modal.resizable(False, False)
        self.settings_modal.configure(fg_color="#2b2b2b")

        self.master.update_idletasks()
        parent_x = self.master.winfo_rootx()
        parent_y = self.master.winfo_rooty()
        button_x = self.settings_button.winfo_rootx() - parent_x
        button_y = self.settings_button.winfo_rooty() - parent_y

        modal_width = 320
        modal_height = 120
        modal_x = (
            parent_x
            + button_x
            - modal_width
            + self.settings_button.winfo_width()
        )
        modal_y = parent_y + button_y - modal_height
        geometry = f"{modal_width}x{modal_height}+{modal_x}+{modal_y}"
        self.settings_modal.geometry(geometry)

        self.settings_modal.transient(self.master)
        self.settings_modal.grab_set()
        self.settings_modal.protocol("WM_DELETE_WINDOW", self._close_settings_modal)

        content = ctk.CTkFrame(self.settings_modal, fg_color="#2b2b2b")
        content.pack(fill="both", expand=True, padx=12, pady=12)

        self._build_slider(content)
        self.settings_modal_open = True

    def _build_slider(self, parent: ctk.CTkFrame) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x")
        row.columnconfigure(1, weight=1)

        ctk.CTkLabel(row, text=self.slider_label).grid(row=0, column=0, padx=(10, 5))

        num_steps = int(round((self.slider_max - self.slider_min) / self.slider_step))
        self.slider = ctk.CTkSlider(
            row,
            from_=self.slider_min,
            to=self.slider_max,
            number_of_steps=num_steps,
            command=lambda value: self._on_slider_change(value),
        )

        default_value = self._get_current_value()
        self.slider.set(default_value)
        self.slider.grid(row=0, column=1, padx=5, sticky="ew")

        self.value_entry = ctk.CTkEntry(row, width=45)
        self.value_entry.insert(0, self._format_value(default_value))
        self.value_entry.grid(row=0, column=2, padx=(5, 10))
        self.value_entry.bind("<Return>", self._on_value_submit)
        self.value_entry.bind("<FocusOut>", self._on_value_focus_out)

    def _get_current_value(self) -> float:
        if self.slider_name in self.calibration_data:
            return self.calibration_data[self.slider_name]
        return self.tk_controls.get(self.slider_name, self.slider_min)

    def _format_value(self, value: float) -> str:
        if self.slider_step < 1:
            return f"{value:.3f}"
        return str(int(round(value)))

    def _on_slider_change(self, value: float) -> None:
        stepped_value = self._apply_step(value)
        self.value_entry.delete(0, "end")
        self.value_entry.insert(0, self._format_value(stepped_value))
        self._persist_value(stepped_value)

    def _on_value_submit(self, event):
        self._apply_entry_value()
        event.widget.winfo_toplevel().focus()

    def _on_value_focus_out(self, _event):
        self._apply_entry_value()

    def _apply_entry_value(self) -> None:
        try:
            value = float(self.value_entry.get())
        except ValueError:
            value = self.slider.get()

        value = max(min(value, self.slider_max), self.slider_min)
        stepped_value = self._apply_step(value)
        self.slider.set(stepped_value)
        self.value_entry.delete(0, "end")
        self.value_entry.insert(0, self._format_value(stepped_value))
        self._persist_value(stepped_value)

    def _apply_step(self, value: float) -> float:
        stepped = round((value - self.slider_min) / self.slider_step) * self.slider_step + self.slider_min
        if self.slider_step >= 1:
            return int(round(stepped))
        return stepped

    def _persist_value(self, value: float) -> None:
        self.tk_controls[self.slider_name] = value
        self.calibration_data[self.slider_name] = value
        refresh_json({self.slider_name: value}, CALIBRATION_FILE)

    def close_modal(self):
        self._close_settings_modal()
