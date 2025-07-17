from PIL import Image, ImageTk
from tkinter import ttk
import cv2
import numpy as np
from src.infrastructure.adapters.display.ui.helpers.ui_helper import ts

def build_video_display(main_frame, shared_frames, webview, log_message):
    video_sec = ttk.LabelFrame(main_frame, text="Exibição de Vídeo / Edges / Object")
    video_sec.grid(row=4, column=0, columnspan=5, sticky="nsew", padx=5, pady=5)
    video_sec.columnconfigure((0,1,2), weight=1)
    lbl_v = ttk.Label(video_sec)
    lbl_e = ttk.Label(video_sec)
    lbl_o = ttk.Label(video_sec)
    lbl_v.grid(row=0, column=0)
    lbl_e.grid(row=0, column=1)
    lbl_o.grid(row=0, column=2)

    def to_tk(img):
        if img is None:
            return None
        if img.ndim == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        return ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)))

    def update_display():
        if not lbl_v.winfo_exists():
            return
        try:
            if "NORMAL_FRAME" in shared_frames:
                img = cv2.imdecode(np.frombuffer(shared_frames["NORMAL_FRAME"], np.uint8), cv2.IMREAD_COLOR)
                i = to_tk(img)
                lbl_v.config(image=i)
                lbl_v.image = i
            if "EDGES_FRAME" in shared_frames:
                img = cv2.imdecode(np.frombuffer(shared_frames["EDGES_FRAME"], np.uint8), cv2.IMREAD_COLOR)
                j = to_tk(img)
                lbl_e.config(image=j)
                lbl_e.image = j
            if "OBJECT_FRAME" in shared_frames:
                img = cv2.imdecode(np.frombuffer(shared_frames["OBJECT_FRAME"], np.uint8), cv2.IMREAD_COLOR)
                k = to_tk(img)
                lbl_o.config(image=k)
                lbl_o.image = k
        except Exception as e:
            log_message(f"Erro ao atualizar imagens: {e}", level="ERROR", prefix=ts())
        video_sec.after(50, update_display)
    update_display()
    return video_sec