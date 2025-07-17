from src.infrastructure.adapters.display.ui.components.trackbars import create_section, create_trackbar_var, create_trackbar_row
from src.infrastructure.constants.video_constants import FRAME_HEIGHT, FRAME_WIDTH
from tkinter import ttk

def build_filter_section(main_frame, tk_controls, vars):
    filter_frame = create_section(main_frame, "Parâmetros de Filtragem", 0, 1)
    for key in ["F_Canny", "S_Canny"]:
        vars[key] = create_trackbar_var(tk_controls, key, "int")
        create_trackbar_row(filter_frame, key, vars[key], 0, 400)

def build_pid_section(main_frame, tk_controls, vars):
    pid_frame = create_section(main_frame, "Parâmetros de Controle (PID)", 0, 2)
    for key, (mn, mx) in {"KP": (0.0, 1.0), "KI": (0.0, 0.1), "KD": (0.0, 0.5)}.items():
        vars[key] = create_trackbar_var(tk_controls, key, "float")
        create_trackbar_row(pid_frame, key, vars[key], mn, mx)

def build_extras_section(main_frame, tk_controls, vars):
    extras_frame = create_section(main_frame, "Extras", 0, 3)
    for key, lim in [("Speed", 255), ("Side", 1), ("Distance", 250), ("Lines", FRAME_HEIGHT)]:
        vars[key] = create_trackbar_var(tk_controls, key, "int")
        create_trackbar_row(extras_frame, key, vars[key], 0, lim)

def build_object_roi_section(main_frame, tk_controls, vars):
    roi_frame = create_section(main_frame, "ROI para Objetos", 0, 4)
    for key in ["Person", "Traffic"]:
        vars[key] = create_trackbar_var(tk_controls, key, "int")
        create_trackbar_row(roi_frame, key, vars[key], 0, 240)

def build_warp_section(main_frame, tk_controls, vars):
    warp_container = ttk.Frame(main_frame)
    warp_container.grid(row=1, column=0, columnspan=5, sticky="nsew", padx=5, pady=5)
    warp_container.columnconfigure(0, weight=1)
    warp_container.columnconfigure(1, weight=1)
    warp_top = ttk.LabelFrame(warp_container, text="Warp Top Points", padding=(10,5))
    warp_top.grid(row=0, column=0, sticky="nsew", padx=(0,5))
    warp_bot = ttk.LabelFrame(warp_container, text="Warp Bottom Points", padding=(10,5))
    warp_bot.grid(row=0, column=1, sticky="nsew", padx=(5,0))
    for pt, frame in [("tl", warp_top), ("tr", warp_top)]:
        for ax in ["x", "y"]:
            key = f"{pt}_{ax}"
            mv = FRAME_WIDTH if ax=='x' else FRAME_HEIGHT
            vars[key] = create_trackbar_var(tk_controls, key, "int")
            create_trackbar_row(frame, key, vars[key], 0, mv)
    for pt, frame in [("bl", warp_bot), ("br", warp_bot)]:
        for ax in ["x", "y"]:
            key = f"{pt}_{ax}"
            mv = FRAME_WIDTH if ax=='x' else FRAME_HEIGHT
            vars[key] = create_trackbar_var(tk_controls, key, "int")
            create_trackbar_row(frame, key, vars[key], 0, mv)
