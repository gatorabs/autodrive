import threading
import tkinter as tk
import os
from PIL import Image, ImageTk
from src.infrastructure.adapters.display.init_ui.components.progress_bar import RoundedProgressbar
from src.infrastructure.utils.setup_system_processor import prepare_initial_flags

class CalibrationUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("System Initialization")
        self.geometry("600x600")
        self.configure(bg="white")

        self.flags_result = {}
        self.flags_ready = {"done": False}
        self.loaded_flags = {}

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.resources_dir = os.path.abspath(os.path.join(self.base_dir, "../../../../../../resources/images"))
        self.img_path = os.path.join(self.resources_dir, "mercedes-benz.png")

        self.original_image = Image.open(self.img_path).resize((250, 250), Image.Resampling.LANCZOS).convert("RGBA")
        self.tk_image = ImageTk.PhotoImage(self.original_image)

        self.container = tk.Frame(self, bg="white")
        self.container.pack(expand=True)

        self.img_label = tk.Label(self.container, image=self.tk_image, bg="white")
        self.img_label.pack(pady=10)

        self.progress = RoundedProgressbar(self.container, width=300, height=20, corner_radius=10)
        self.progress.pack(pady=(0, 10))

        self.start_loading()

    def update_progress(self, value):
        self.progress.set_value(value)

    def show_flags(self):
        self.flags_result = self.loaded_flags
        self.fade_out_logo()

    def fade_in_logo(self, alpha=0.0):
        if alpha >= 1.0:
            self.wait_for_flags()
            return

        faded = self.original_image.copy()
        alpha_channel = faded.split()[3].point(lambda p: int(p * alpha))
        faded.putalpha(alpha_channel)
        self.tk_image = ImageTk.PhotoImage(faded)
        self.img_label.configure(image=self.tk_image)
        self.after(50, lambda: self.fade_in_logo(alpha + 0.1))

    def wait_for_flags(self):
        if self.flags_ready["done"]:
            self.progress.set_value(100)
            self.show_flags()
        else:
            self.after(100, self.wait_for_flags)

    def fade_out_logo(self, alpha=1.0):
        if alpha <= 0:
            self.img_label.pack_forget()
            self.progress.pack_forget()
            self.destroy()
            return

        faded = self.original_image.copy()
        alpha_channel = faded.split()[3].point(lambda p: int(p * alpha))
        faded.putalpha(alpha_channel)
        self.tk_image = ImageTk.PhotoImage(faded)
        self.img_label.configure(image=self.tk_image)
        self.after(50, lambda: self.fade_out_logo(alpha - 0.05))

    def load_flags_in_background(self):
        def task():
            def thread_safe_progress(value):
                self.after(0, lambda: self.update_progress(value))

            flags = prepare_initial_flags(progress_callback=thread_safe_progress)
            self.loaded_flags.update(flags)
            self.flags_ready["done"] = True

        threading.Thread(target=task, daemon=True).start()

    def start_loading(self):
        self.after(0, self.load_flags_in_background)
        self.fade_in_logo()