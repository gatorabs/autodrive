import customtkinter as ctk
from src.infrastructure.adapters.calibration.calibration_repository import (
    load_data,
    refresh_json,
    save_data,
)
from src.infrastructure.constants.ui_constants.file_constants import DEFAULTS_FILE

class FloatingWidget(ctk.CTkFrame):
    """Small widget with buttons for saving and restoring defaults."""
    def __init__(self, master, tk_controls, **kwargs):
        super().__init__(master, fg_color="#2b2b2b", **kwargs)

        # ratios calculated from the original 1920x1080 layout
        self._offset_x_ratio = 700 / 1920
        self._modal_offset_x_ratio = 693 / 1920
        self._offset_y_ratio = 27 / 1080
        self._max_width_ratio = 267 / 1920
        self._max_height_ratio = 40 / 1080

        # place using proportions instead of absolute pixels
        self.place(
            relx=1 - self._offset_x_ratio,
            rely=1 - self._offset_y_ratio,
            anchor="se",
        )

        self.save_data = save_data
        self.load_data = load_data
        self.tk_controls = tk_controls
        self.DEFAULTS_FILE = DEFAULTS_FILE
        self.button_colors = "#2b2b2b"

        self.modal = None
        self.modal_open = False
        self.modal_width_ratio = 0

        self.scale = ctk.get_widget_scaling()
        self.max_width = 0
        self.max_height = 0

        self.floating_button = ctk.CTkButton(
            self,
            text="📂",
            corner_radius=10,
            command=self.toggle_modal,
        )
        self.floating_button.pack()

        # update sizes once the master has been drawn and when it changes
        self.after(0, self._update_geometry)
        self.master.bind("<Configure>", self._update_geometry)

    def _update_geometry(self, event=None):
        """Recalculate sizes and positions based on the master's size and scaling."""
        width = self.master.winfo_width()
        height = self.master.winfo_height()
        self.scale = ctk.get_widget_scaling()

        self.max_width = int(width * self._max_width_ratio * self.scale)
        self.max_height = int(height * self._max_height_ratio * self.scale)

        btn_size = self.max_height
        self.floating_button.configure(
            width=btn_size,
            height=btn_size,
            font=ctk.CTkFont(size=int(15 * self.scale)),
        )

        if self.modal:
            self.modal.place_configure(
                relx=1 - self._modal_offset_x_ratio,
                rely=1 - self._offset_y_ratio,
                anchor="sw",
                relheight=self._max_height_ratio,
            )
            btn_width = int(width * 125 / 1920 * self.scale)
            self.button1.configure(width=btn_width, height=self.max_height)
            self.button2.configure(width=btn_width, height=self.max_height)

    def toggle_modal(self):
        if self.modal_open:
            self._start_closing()
        else:
            self._start_opening()

    def close_modal(self):
        if self.modal_open:
            self._start_closing()

    def _start_opening(self):
        if self.modal:
            self.modal.destroy()

        self.modal = ctk.CTkFrame(
            self.master,
            fg_color="#2b2b2b",
            corner_radius=0,
            border_width=2,
            border_color="#FFFFFF",
        )
        self.modal.place(
            relx=1 - self._modal_offset_x_ratio,
            rely=1 - self._offset_y_ratio,
            anchor="sw",
        )
        self.modal.place_configure(relwidth=0, relheight=self._max_height_ratio)

        btn_frame = ctk.CTkFrame(self.modal, fg_color="#2b2b2b")
        btn_frame.pack(fill="both", expand=True, padx=5)
        self.button1 = ctk.CTkButton(
            btn_frame,
            text="Salvar Padrão",
            command=self.button_1_action,
            text_color="#1DBF08",
            border_color="#1DBF08",
            border_width=2,
            fg_color=self.button_colors,
        )
        self.button2 = ctk.CTkButton(
            btn_frame,
            text="Restaurar Padrão",
            command=self.button_2_action,
            text_color="#BF081D",
            border_color="#BF081D",
            border_width=2,
            fg_color=self.button_colors,
        )
        self.button1.pack(side="left", padx=(3, 5), pady=5)
        self.button2.pack(side="left", padx=(5, 3), pady=5)

        self._update_geometry()

        self.modal_width_ratio = 0
        self.modal_open = True
        self._animate_open()

    def _animate_open(self):
        if not self.modal:
            return
        if self.modal_width_ratio < self._max_width_ratio:
            self.modal_width_ratio += 10 / 1920
            self.modal.place_configure(relwidth=self.modal_width_ratio)
            self.after(10, self._animate_open)

    def _start_closing(self):
        if hasattr(self, "button1"):
            self.button1.pack_forget()
            self.button2.pack_forget()
        self._animate_close()

    def _animate_close(self):
        if not self.modal:
            return
        if self.modal_width_ratio > 0:
            self.modal_width_ratio -= 10 / 1920
            if self.modal_width_ratio < 0:
                self.modal_width_ratio = 0
            self.modal.place_configure(relwidth=self.modal_width_ratio)
            self.after(10, self._animate_close)
        else:
            self.modal.destroy()
            self.modal = None
            self.modal_open = False

    def button_1_action(self):
        refresh_json(self.tk_controls, self.DEFAULTS_FILE, only_existing_keys=True)
        self._start_closing()

    def button_2_action(self):
        self.master.restore_defaults()
        self._start_closing()
