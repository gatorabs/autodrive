import customtkinter as ctk
from PIL import Image
from customtkinter import CTkImage
import io

FRAME_WIDTH = 360
FRAME_HEIGHT = 203

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
        self.pack_propagate(False)
        self.tk_controls = tk_controls

        ctk.CTkLabel(self, text="Filtros", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0, 10))

        # F_Canny
        f_row = ctk.CTkFrame(self)
        f_row.pack(fill="x", padx=20, pady=2)
        f_row.columnconfigure(1, weight=1)

        ctk.CTkLabel(f_row, text="F_Canny").grid(row=0, column=0, padx=(10, 5))
        self.f_canny_slider = ctk.CTkSlider(f_row, from_=0, to=255, number_of_steps=255, command=self.update_f_canny)
        self.f_canny_slider.set(self.tk_controls.get("F_Canny", 20))
        self.f_canny_slider.grid(row=0, column=1, padx=5, sticky="ew")

        self.f_canny_value = ctk.CTkLabel(f_row, text=str(self.f_canny_slider.get()), fg_color="transparent",
                                          bg_color="transparent")
        self.f_canny_value.grid(row=0, column=2, padx=(5, 10))

        # S_Canny
        s_row = ctk.CTkFrame(self)
        s_row.pack(fill="x", padx=20, pady=2)
        s_row.columnconfigure(1, weight=1)

        ctk.CTkLabel(s_row, text="S_Canny").grid(row=0, column=0, padx=(10, 5))
        self.s_canny_slider = ctk.CTkSlider(s_row, from_=0, to=255, number_of_steps=255, command=self.update_s_canny)
        self.s_canny_slider.set(self.tk_controls.get("S_Canny", 152))
        self.s_canny_slider.grid(row=0, column=1, padx=5, sticky="ew")

        self.s_canny_value = ctk.CTkLabel(s_row, text=str(self.s_canny_slider.get()), fg_color="transparent",
                                          bg_color="transparent")
        self.s_canny_value.grid(row=0, column=2, padx=(5, 10))

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
        self.VIDEO_WIDTH = FRAME_WIDTH
        self.GAP = 20
        self.TOTAL_WIDTH = self.VIDEO_WIDTH * 3 + self.GAP * 4
        self.TOTAL_HEIGHT = 350

        self.geometry(f"{self.TOTAL_WIDTH}x{self.TOTAL_HEIGHT}")
        self.minsize(self.TOTAL_WIDTH, self.TOTAL_HEIGHT)
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

        self.normal_frame.grid(row=0, column=0, padx=10, pady=(10,2))
        self.edges_frame.grid(row=0, column=1, padx=10, pady=(10,2))
        self.object_frame.grid(row=0, column=2, padx=10, pady=(10,2))

        # Seção de Filtros
        self.filters_container = ctk.CTkFrame(self)
        self.filters_container.grid(row=1, column=1, pady=(2, 5))
        self.filters_container.configure(width=self.VIDEO_WIDTH, height=110)
        self.filters_container.pack_propagate(False)

        self.filters = FilterControls(self.filters_container, self.tk_controls)
        self.filters.pack(fill="both", expand=True)
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
