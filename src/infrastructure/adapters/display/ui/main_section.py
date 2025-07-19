import customtkinter as ctk
from PIL import Image
from customtkinter import CTkImage
import multiprocessing as mp
import io

FRAME_WIDTH = 240
FRAME_HEIGHT = 135

class VideoFrame(ctk.CTkFrame):
    def __init__(self, master, title="Frame", **kwargs):
        super().__init__(master, **kwargs)
        self.label = ctk.CTkLabel(self, text=title)
        self.label.pack()
        self.image_label = ctk.CTkLabel(self, text="")
        self.image_label.pack()

    def update_image(self, image_bytes):
        if image_bytes:
            image = Image.open(io.BytesIO(image_bytes)).resize((FRAME_WIDTH, FRAME_HEIGHT))
            ctk_image = CTkImage(light_image=image, size=(FRAME_WIDTH, FRAME_HEIGHT))
            self.image_label.configure(image=ctk_image)
            self.image_label.image = ctk_image


class FilterControls(ctk.CTkFrame):
    def __init__(self, master, tk_controls, **kwargs):
        super().__init__(master, **kwargs)
        self.tk_controls = tk_controls

        ctk.CTkLabel(self, text="Filtros", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0, 10))

        # F_Canny
        self.f_canny_frame = ctk.CTkFrame(self)
        self.f_canny_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(self.f_canny_frame, text="F_Canny").pack(side="left")
        self.f_canny_slider = ctk.CTkSlider(
            self.f_canny_frame, from_=0, to=255, number_of_steps=255,
            command=self.update_f_canny
        )
        self.f_canny_slider.set(self.tk_controls.get("F_Canny", 20))
        self.f_canny_slider.pack(side="left", fill="x", expand=True, padx=(10, 10))

        self.f_canny_value = ctk.CTkLabel(self.f_canny_frame, text=str(self.f_canny_slider.get()))
        self.f_canny_value.pack(side="left")

        # S_Canny
        self.s_canny_frame = ctk.CTkFrame(self)
        self.s_canny_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(self.s_canny_frame, text="S_Canny").pack(side="left")
        self.s_canny_slider = ctk.CTkSlider(
            self.s_canny_frame, from_=0, to=255, number_of_steps=255,
            command=self.update_s_canny
        )
        self.s_canny_slider.set(self.tk_controls.get("S_Canny", 152))
        self.s_canny_slider.pack(side="left", fill="x", expand=True, padx=(10, 10))

        self.s_canny_value = ctk.CTkLabel(self.s_canny_frame, text=str(self.s_canny_slider.get()))
        self.s_canny_value.pack(side="left")

    def update_f_canny(self, value):
        value = int(value)
        self.tk_controls["F_Canny"] = value
        self.f_canny_value.configure(text=str(value))

    def update_s_canny(self, value):
        value = int(value)
        self.tk_controls["S_Canny"] = value
        self.s_canny_value.configure(text=str(value))

class MainApp(ctk.CTk):
    def __init__(self, shared_frames, tk_controls):
        super().__init__()
        self.title("Visualizador de Frames com Filtros")
        self.geometry("850x400")
        self.shared_frames = shared_frames
        self.tk_controls = tk_controls

        # Layout geral
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure((0, 1, 2), weight=1)

        # Vídeos
        self.normal_frame = VideoFrame(self, "NORMAL_FRAME")
        self.edges_frame = VideoFrame(self, "EDGES_FRAME")
        self.object_frame = VideoFrame(self, "OBJECT_FRAME")

        self.normal_frame.grid(row=0, column=0, padx=10, pady=10)
        self.edges_frame.grid(row=0, column=1, padx=10, pady=10)
        self.object_frame.grid(row=0, column=2, padx=10, pady=10)

        # Seção de Filtros
        self.filters = FilterControls(self, self.tk_controls)
        self.filters.grid(row=1, column=0, columnspan=3, pady=10, sticky="ew")

        self.update_loop()

    def update_loop(self):
        try:
            self.normal_frame.update_image(self.shared_frames.get("NORMAL_FRAME"))
            self.edges_frame.update_image(self.shared_frames.get("EDGES_FRAME"))
            self.object_frame.update_image(self.shared_frames.get("OBJECT_FRAME"))
        except Exception as e:
            print("Erro ao atualizar frames:", e)

        self.after(33, self.update_loop)  # ~30 FPS


def launch_homepage(shared_frames, tk_controls):
    app = MainApp(shared_frames, tk_controls)
    app.mainloop()
