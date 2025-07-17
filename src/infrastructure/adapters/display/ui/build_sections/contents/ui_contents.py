from src.infrastructure.adapters.display.ui.components.trackbars import create_trackbar_var, create_trackbar_row
from src.infrastructure.constants.video_constants import FRAME_HEIGHT
import tkinter as tk
from tkinter import ttk
from src.infrastructure.adapters.display.ui.components.flags import make_flag_command

def build_filter_section_content(parent, tk_controls, vars):
    for key in ["F_Canny", "S_Canny"]:
        vars[key] = create_trackbar_var(tk_controls, key, "int")
        create_trackbar_row(parent, key, vars[key], 0, 400)

def build_pid_section_content(parent, tk_controls, vars):
    for key, (mn, mx) in {"KP": (0.0, 1.0), "KI": (0.0, 0.1), "KD": (0.0, 0.5)}.items():
        vars[key] = create_trackbar_var(tk_controls, key, "float")
        create_trackbar_row(parent, key, vars[key], mn, mx)

def build_extras_section_content(parent, tk_controls, vars):
    for key, lim in [("Speed", 255), ("Side", 1), ("Distance", 250), ("Lines", FRAME_HEIGHT)]:
        vars[key] = create_trackbar_var(tk_controls, key, "int")
        create_trackbar_row(parent, key, vars[key], 0, lim)

def build_roi_section_content(parent, tk_controls, vars):
    for key in ["Person", "Traffic"]:
        vars[key] = create_trackbar_var(tk_controls, key, "int")
        create_trackbar_row(parent, key, vars[key], 0, 240)

def build_flag_section_content(parent, tk_controls, shared_controls, vars):
    checkboxes = [("SHOW_ROI", "Toggle ROI"),
                  ("SHOW_INFO", "Toggle Info"),
                  ("WEBVIEW", "Toggle Webview"),
                  ("NEW_PID", "Toggle PID V2"),
                  ("SEND_LOGS", "Show Send-Logs")]

    for key, label in checkboxes:
        var = tk.BooleanVar(value=tk_controls.get(key, False))
        vars[key] = var
        ttk.Checkbutton(parent, text=label, variable=var,
                        command=make_flag_command(tk_controls, vars, key, var, shared_controls=shared_controls)
                       ).pack(fill="x", pady=2)