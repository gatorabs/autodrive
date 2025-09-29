import customtkinter as ctk
from src.infrastructure.data.repository.calibration_repository import save_data, load_data, refresh_json
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
            self.close_modal()
            return
        self._open_modal()

    def close_modal(self):
        if self.modal_open:
            if self.modal:
                self.modal.grab_release()
                self.modal.destroy()
            self.modal = None
            self.modal_open = False

    def _open_modal(self):
        if self.modal:
            try:
                self.modal.destroy()
            except ctk.TclError:
                pass

        self.modal = ctk.CTkToplevel(self.master)
        self.modal.title("Opções de Salvar")
        self.modal.resizable(False, False)
        self.modal.configure(fg_color="#2b2b2b")

        # Position the modal near the floating button
        self.master.update_idletasks()
        parent_x = self.master.winfo_rootx()
        parent_y = self.master.winfo_rooty()
        button_x = self.floating_button.winfo_rootx() - parent_x
        button_y = self.floating_button.winfo_rooty() - parent_y
        modal_x = parent_x + button_x - self.max_width
        modal_y = parent_y + button_y - self.max_height
        self.modal.geometry(f"{self.max_width}x{self.max_height+30}+{modal_x}+{modal_y}")

        self.modal.transient(self.master)
        self.modal.grab_set()
        self.modal.protocol("WM_DELETE_WINDOW", self.close_modal)

        btn_frame = ctk.CTkFrame(self.modal, fg_color="#2b2b2b")
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
            height=self.max_height,
        )
        self.button2 = ctk.CTkButton(
            btn_frame,
            text="Restaurar Padrão",
            command=self.button_2_action,
            width=125,
            height=self.max_height,
            text_color="#BF081D",
            border_color="#BF081D",
            border_width=2,
            fg_color=self.button_colors,
        )
        self.button1.pack(side="left", padx=(0, 10))
        self.button2.pack(side="left")

        self.modal_open = True

    def button_1_action(self):
        refresh_json(self.tk_controls, self.DEFAULTS_FILE, only_existing_keys=True)
        self.close_modal()

    def button_2_action(self):
        self.master.restore_defaults()
        self.close_modal()
