import tkinter as tk
from tkinter import ttk
import os
from src.infrastructure.constants.flags_constants import flags
from src.infrastructure.adapters.video.begin_the_video import (
    detect_camera_indices,
    get_video_files_from_folder,
)
from src.infrastructure.adapters.serial.serial_comm import SerialCommunicator
from src.infrastructure.logging.logger import Logger
from src.infrastructure.constants.ui_constants.file_constants import DEFAULT_UI_PATH
from src.infrastructure.adapters.calibration.calibration_repository import save_data, load_data

logger = Logger("CalibrationUI", verbose=True)

def setup_flag_interface():
    root = tk.Tk()
    root.title("Configure Shared Controls")
    root.geometry("420x450")

    style = ttk.Style()
    style.configure("TButton", font=("Arial", 10))
    style.configure("TCheckbutton", font=("Arial", 10))
    style.configure("TLabel", font=("Arial", 10))

    main_frame = ttk.Frame(root, padding=10)
    main_frame.pack(fill="both", expand=True)

    saved_defaults = load_data(DEFAULT_UI_PATH)

    com_defaults = {
        "SECURITY_COM": saved_defaults.get("SECURITY_COM"),
        "SENDER_COM": saved_defaults.get("SENDER_COM")
    }

    video_defaults = {
        "LANE_SOURCE": saved_defaults.get("LANE_SOURCE"),
        "OBJECT_SOURCE": saved_defaults.get("OBJECT_SOURCE")
    }

    bool_vars = {}
    com_vars = {}
    video_vars = {}

    # === Flags ===
    flags_frame = ttk.LabelFrame(main_frame, text="Opções de Controle", padding=10)
    flags_frame.pack(fill="x", padx=5, pady=10)

    for name, default in flags.items():
        var = tk.BooleanVar(value=saved_defaults.get(name, default))
        ttk.Checkbutton(flags_frame, text=name, variable=var).pack(anchor="w", pady=2)
        bool_vars[name] = var

    # === COM Ports ===
    com_frame = ttk.LabelFrame(main_frame, text="Portas de Comunicação", padding=10)
    com_frame.pack(fill="x", padx=5, pady=10)

    available_coms = SerialCommunicator.list_available_ports()

    for name, default in com_defaults.items():
        row = ttk.Frame(com_frame)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=name, width=16).pack(side="left")

        combo = ttk.Combobox(row, values=available_coms, width=30)
        combo.set(default if default in available_coms else (available_coms[0] if available_coms else default))
        combo.pack(side="left", fill="x", expand=True)
        com_vars[name] = combo

    # === Fontes de Vídeo ===
    video_frame = ttk.LabelFrame(main_frame, text="Fontes de Vídeo ou Câmera", padding=10)
    video_frame.pack(fill="x", padx=5, pady=10)

    detected_cameras = detect_camera_indices()

    raw_sources = get_video_files_from_folder() + detected_cameras
    combined_sources = [os.path.normpath(s) if isinstance(s, str) else s for s in raw_sources]

    def create_source_selector(name, default):
        row = ttk.Frame(video_frame)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=name, width=16).pack(side="left")

        path_to_label = {}
        label_to_path = {}

        for item in combined_sources:
            label = f"Camera {item}" if isinstance(item, int) else os.path.basename(item)
            path = item
            path_to_label[path] = label
            label_to_path[label] = path

        labels = list(label_to_path.keys())

        combo = ttk.Combobox(row, values=labels, width=40)
        default_norm = os.path.normpath(default)
        default_label = path_to_label.get(default_norm, labels[0] if labels else "")
        combo.set(default_label)
        combo.pack(side="left", fill="x", expand=True)

        video_vars[name] = (combo, label_to_path)

    create_source_selector("LANE_SOURCE", video_defaults["LANE_SOURCE"])
    create_source_selector("OBJECT_SOURCE", video_defaults["OBJECT_SOURCE"])

    result = {}

    def submit():
        for name, var in bool_vars.items():
            result[name] = var.get()
        for name, widget in com_vars.items():
            result[name] = widget.get()
        for name, (widget, label_to_path) in video_vars.items():
            selected_label = widget.get()
            val = label_to_path.get(selected_label, selected_label)
            result[name] = int(val) if isinstance(val, str) and val.isdigit() else val

        result["DETECTED_CAMERAS"] = detected_cameras
        save_data(result, DEFAULT_UI_PATH)
        root.quit()

    ttk.Button(main_frame, text="Aplicar e Iniciar", command=submit).pack(pady=15, fill="x")

    root.mainloop()
    root.destroy()
    return result
