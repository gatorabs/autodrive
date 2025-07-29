import customtkinter as ctk
from src.infrastructure.adapters.calibration.calibration_repository import save_data, load_data, refresh_json
from src.infrastructure.constants.ui_constants.file_constants import DEFAULTS_FILE

class FloatingWidget(ctk.CTkFrame):
    """Small widget with buttons for saving and restoring defaults."""
    def __init__(self, master, tk_controls, **kwargs):
        super().__init__(master, fg_color="#2b2b2b", **kwargs)
        self.place(relx=1.0, rely=1.0, anchor="se", x=-700, y=-27)

        self.save_data = save_data
        self.load_data = load_data
        self.tk_controls = tk_controls
        self.DEFAULTS_FILE = DEFAULTS_FILE
        self.button_colors = "#2b2b2b"

        self.modal = None
        self.modal_open = False
        self.modal_width = 0

        self.max_width = 267
        self.max_height = 40

        self.floating_button = ctk.CTkButton(
            self,
            text="📂",
            width=40,
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(size=15),
            command=self.toggle_modal,
        )
        self.floating_button.pack()

    def toggle_modal(self):
        if self.modal_open:
            self._start_closing()
        else:
            self._start_opening()

    def _start_opening(self):
        if self.modal:
            self.modal.destroy()

        self.modal = ctk.CTkFrame(self.master, fg_color="#2b2b2b", corner_radius=0, border_width=2, border_color="#FFFFFF")
        self.modal.place(relx=1.0, rely=1.0, anchor="sw", x=-693, y=-27)
        self.modal.place_configure(width=0, height=self.max_height)

        btn_frame = ctk.CTkFrame(self.modal, fg_color="#2b2b2b")
        btn_frame.pack(fill="both", expand=True, padx=5)
        self.button1 = ctk.CTkButton(
            btn_frame, text="Salvar Padrão",
            command=self.button_1_action, text_color="#1DBF08", border_color="#1DBF08", border_width=2, fg_color=self.button_colors,
            width=125, height=self.max_height,
        )
        self.button2 = ctk.CTkButton(
            btn_frame, text="Restaurar Padrão",
            command=self.button_2_action,
            width=125, height=self.max_height, text_color="#BF081D", border_color="#BF081D", border_width=2,fg_color=self.button_colors
        )
        self.button1.pack(side="left", padx=(3, 5), pady=5)
        self.button2.pack(side="left", padx=(5, 3), pady=5)

        self.modal_width = 0
        self.modal_open = True
        self._animate_open()

    def _animate_open(self):
        if not self.modal:
            return
        if self.modal_width < self.max_width:
            self.modal_width += 10
            self.modal.place_configure(width=self.modal_width)
            self.after(10, self._animate_open)

    def _start_closing(self):
        if hasattr(self, "button1"):
            self.button1.pack_forget()
            self.button2.pack_forget()
        self._animate_close()

    def _animate_close(self):
        if not self.modal:
            return
        if self.modal_width > 0:
            self.modal_width -= 10
            self.modal.place_configure(width=self.modal_width)
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
