import tkinter as tk
from tkinter import ttk
import os
from src.infrastructure.constants.flags_constants import flags
from src.infrastructure.adapters.video.begin_the_video import (
    detect_camera_indices,
    get_video_files_from_folder,
)
from src.infrastructure.adapters.serial.serial_comm import SerialCommunicator

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

    # === Valores padrão ===
    com_defaults = {
        "SECURITY_COM": "COM5",
        "SENDER_COM": "COM3"
    }

    video_defaults = {
        "LANE_SOURCE": "resources/test_videos/road_video_test_1.mp4",
        "OBJECT_SOURCE": "resources/test_videos/people_video_test_1.mp4"
    }

    bool_vars = {}
    com_vars = {}
    video_vars = {}

    # === Flags ===
    flags_frame = ttk.LabelFrame(main_frame, text="Opções de Controle", padding=10)
    flags_frame.pack(fill="x", padx=5, pady=10)

    for name, default in flags.items():
        var = tk.BooleanVar(value=default)
        ttk.Checkbutton(flags_frame, text=name, variable=var).pack(anchor="w", pady=2)
        bool_vars[name] = var

    # === Comunicação (COM ports) ===
    com_frame = ttk.LabelFrame(main_frame, text="Portas de Comunicação", padding=10)
    com_frame.pack(fill="x", padx=5, pady=10)

    available_coms = SerialCommunicator.list_available_ports()

    for name, default in com_defaults.items():
        row = ttk.Frame(com_frame)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=name, width=16).pack(side="left")

        combo = ttk.Combobox(row, values=available_coms, width=30)
        if default in available_coms:
            combo.set(default)
        elif available_coms:
            combo.set(available_coms[0])
        else:
            combo.set(default)
        combo.pack(side="left", fill="x", expand=True)
        com_vars[name] = combo

    # === Fontes de Vídeo ===
    video_frame = ttk.LabelFrame(main_frame, text="Fontes de Vídeo ou Câmera", padding=10)
    video_frame.pack(fill="x", padx=5, pady=10)

    raw_sources = get_video_files_from_folder() + detect_camera_indices()
    combined_sources = [os.path.normpath(s) if isinstance(s, str) else s for s in raw_sources]

    def create_source_selector(name, default):
        row = ttk.Frame(video_frame)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=name, width=16).pack(side="left")

        # Cria dicionários de mapeamento para exibição e valor real
        path_to_label = {}
        label_to_path = {}

        for item in combined_sources:
            if isinstance(item, int):
                label = f"Camera {item}"
                path = item
            else:
                label = os.path.basename(item)
                path = item
            path_to_label[path] = label
            label_to_path[label] = path

        labels = list(label_to_path.keys())

        combo = ttk.Combobox(row, values=labels, width=40)

        default_norm = os.path.normpath(default)
        default_label = path_to_label.get(default_norm, labels[0])

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
        root.quit()

    ttk.Button(main_frame, text="Aplicar e Iniciar", command=submit).pack(pady=15, fill="x")

    root.mainloop()
    root.destroy()
    return result
