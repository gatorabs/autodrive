import customtkinter as ctk

from src.infrastructure.data.repository.calibration_repository import (
    load_data,
    refresh_json,
    save_data,
)
from src.infrastructure.constants.ui_constants.file_constants import DEFAULTS_FILE
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
        self.place(relx=1.0, rely=1.0, anchor="se", x=-700, y=-27)

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
        self.checkbox_modal_width = 420
        self.checkbox_modal_height = 170

        buttons_row = ctk.CTkFrame(self, fg_color="transparent")
        buttons_row.pack(anchor="e")

        self.checkboxes_button = ctk.CTkButton(
            buttons_row,
            text="☑️",
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
