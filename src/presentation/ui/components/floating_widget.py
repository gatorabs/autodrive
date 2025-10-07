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

CUSTOM_CONF_OVERRIDES_KEY = "CUSTOM_CONF_OVERRIDES"
CUSTOM_CONF_METADATA_KEY = "CUSTOM_CONF_METADATA"
CUSTOM_CONF_DEFAULT_KEY = "CUSTOM_CONF_DEFAULT"


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
        self.custom_conf_modal = None
        self.custom_conf_modal_open = False
        self.save_modal_width = 267
        self.save_modal_height = 70
        self.checkbox_modal_width = 460
        self.checkbox_modal_height = 170
        self.custom_conf_modal_width = 420
        self.custom_conf_modal_height = 260

        buttons_row = ctk.CTkFrame(self, fg_color="transparent")
        buttons_row.pack(anchor="e")

        self.custom_conf_button = ctk.CTkButton(
            buttons_row,
            text="🎯",
            width=40,
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(size=15),
            command=self.toggle_custom_conf_modal,
        )
        self.custom_conf_button.pack(side="right", padx=(0, 8))

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
        self._close_custom_conf_modal()
        self._open_save_modal()

    def toggle_checkbox_modal(self):
        if self.checkbox_modal_open:
            self._close_checkbox_modal()
            return
        self._close_save_modal()
        self._close_custom_conf_modal()
        self._open_checkbox_modal()

    def toggle_custom_conf_modal(self):
        if self.custom_conf_modal_open:
            self._close_custom_conf_modal()
            return
        self._close_checkbox_modal()
        self._close_save_modal()
        self._open_custom_conf_modal()

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

    def _close_custom_conf_modal(self):
        if self.custom_conf_modal_open and self.custom_conf_modal:
            try:
                self.custom_conf_modal.grab_release()
                self.custom_conf_modal.destroy()
            except ctk.TclError:
                pass
            finally:
                self.custom_conf_modal = None
                self.custom_conf_modal_open = False

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

    def _open_custom_conf_modal(self):
        if self.custom_conf_modal:
            try:
                self.custom_conf_modal.destroy()
            except ctk.TclError:
                pass

        self.custom_conf_modal = ctk.CTkToplevel(self.master)
        self.custom_conf_modal.title("Confiança Objetos Customizados")
        self.custom_conf_modal.resizable(False, False)
        self.custom_conf_modal.configure(fg_color="#2b2b2b")

        self.master.update_idletasks()
        parent_x = self.master.winfo_rootx()
        parent_y = self.master.winfo_rooty()
        button_x = self.custom_conf_button.winfo_rootx() - parent_x
        button_y = self.custom_conf_button.winfo_rooty() - parent_y
        modal_x = (
            parent_x
            + button_x
            - self.custom_conf_modal_width
            + self.custom_conf_button.winfo_width()
        )
        modal_y = parent_y + button_y - self.custom_conf_modal_height
        geometry = (
            f"{self.custom_conf_modal_width}x{self.custom_conf_modal_height}"
            f"+{modal_x}+{modal_y}"
        )
        self.custom_conf_modal.geometry(geometry)

        self.custom_conf_modal.transient(self.master)
        self.custom_conf_modal.grab_set()
        self.custom_conf_modal.protocol(
            "WM_DELETE_WINDOW", self._close_custom_conf_modal
        )

        container = ctk.CTkFrame(self.custom_conf_modal, fg_color="#2b2b2b")
        container.pack(fill="both", expand=True, padx=16, pady=16)

        metadata = self.tk_controls.get(CUSTOM_CONF_METADATA_KEY, {}) or {}
        overrides = self.tk_controls.get(CUSTOM_CONF_OVERRIDES_KEY, {}) or {}
        default_conf = self.tk_controls.get(CUSTOM_CONF_DEFAULT_KEY, 0.35)

        if not isinstance(metadata, dict):
            metadata = {}
        if not isinstance(overrides, dict):
            overrides = {}
        try:
            default_conf = float(default_conf)
        except (TypeError, ValueError):
            default_conf = 0.35

        if not metadata:
            ctk.CTkLabel(
                container,
                text="Nenhum modelo customizado disponível.",
            ).pack(fill="x")
        else:
            info_frame = ctk.CTkScrollableFrame(
                container,
                fg_color="#2b2b2b",
                width=self.custom_conf_modal_width - 32,
                height=self.custom_conf_modal_height - 60,
            )
            info_frame.pack(fill="both", expand=True)

            sorted_items = sorted(
                metadata.items(),
                key=lambda item: (
                    (item[1] or {}).get("model", ""),
                    (item[1] or {}).get("label", item[0]),
                ),
            )

            for key, meta in sorted_items:
                label = (meta or {}).get("label", key)
                model = (meta or {}).get("model")
                display = f"{label} ({model})" if model else label
                percent_value = float(overrides.get(key, default_conf)) * 100.0
                percent_value = max(5.0, min(99.0, percent_value))

                row = ctk.CTkFrame(info_frame, fg_color="#1f1f1f")
                row.pack(fill="x", padx=4, pady=4)
                row.columnconfigure(1, weight=1)

                ctk.CTkLabel(row, text=display).grid(
                    row=0,
                    column=0,
                    padx=(12, 8),
                    pady=6,
                    sticky="w",
                )

                slider = ctk.CTkSlider(
                    row,
                    from_=5,
                    to=99,
                    number_of_steps=94,
                    command=lambda value, conf_key=key: self._on_conf_slider_change(
                        conf_key, value
                    ),
                )
                slider.set(percent_value)
                slider.grid(row=0, column=1, padx=8, sticky="ew")

                entry = ctk.CTkEntry(row, width=55)
                entry.insert(0, f"{percent_value:.0f}%")
                entry.grid(row=0, column=2, padx=(8, 12))

                slider.configure(
                    command=lambda value, conf_key=key, entry_widget=entry: self._on_conf_slider_change(
                        conf_key, value, entry_widget
                    )
                )

        self.custom_conf_modal_open = True

    def _on_conf_slider_change(self, conf_key: str, value: float, entry_widget=None):
        percent = round(value)
        if entry_widget is not None:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, f"{percent}%")

        confidence = max(0.05, min(0.99, percent / 100.0))
        overrides = dict(self.tk_controls.get(CUSTOM_CONF_OVERRIDES_KEY, {}) or {})
        if overrides.get(conf_key) == confidence:
            return

        overrides[conf_key] = confidence
        self.tk_controls[CUSTOM_CONF_OVERRIDES_KEY] = overrides
        try:
            refresh_json({CUSTOM_CONF_OVERRIDES_KEY: overrides}, CALIBRATION_FILE)
        except Exception:
            pass

    def button_1_action(self):
        refresh_json(self.tk_controls, self.DEFAULTS_FILE, only_existing_keys=True)
        self._close_save_modal()

    def button_2_action(self):
        self.master.restore_defaults()
        self._close_save_modal()
