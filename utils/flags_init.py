import tkinter as tk
from tkinter import ttk
from utils.constants import flags
from utils.camera_utils import detect_camera_indices, get_video_files_from_folder

def setup_flag_interface():
    root = tk.Tk()
    root.title("Configure Shared Controls")
    root.geometry("500x450")

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
        "LANE_SOURCE": "test_videos/pista_01.mov",
        "OBJECT_SOURCE": "test_videos/people.mp4"
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

    # === Comunicação ===
    com_frame = ttk.LabelFrame(main_frame, text="Portas de Comunicação", padding=10)
    com_frame.pack(fill="x", padx=5, pady=10)

    for name, default in com_defaults.items():
        row = ttk.Frame(com_frame)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=name, width=16).pack(side="left")
        entry = ttk.Entry(row)
        entry.insert(0, default)
        entry.pack(side="left", fill="x", expand=True)
        com_vars[name] = entry

    # === Fontes de Vídeo ===
    video_frame = ttk.LabelFrame(main_frame, text="Fontes de Vídeo ou Câmera", padding=10)
    video_frame.pack(fill="x", padx=5, pady=10)

    combined_sources = get_video_files_from_folder() + detect_camera_indices()

    def create_source_selector(name, default):
        row = ttk.Frame(video_frame)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=name, width=16).pack(side="left")

        combo = ttk.Combobox(row, values=combined_sources, width=40)
        combo.set(default if default in combined_sources else combined_sources[0])
        combo.pack(side="left", fill="x", expand=True)
        video_vars[name] = combo

    create_source_selector("LANE_SOURCE", video_defaults["LANE_SOURCE"])
    create_source_selector("OBJECT_SOURCE", video_defaults["OBJECT_SOURCE"])

    result = {}

    def submit():
        for name, var in bool_vars.items():
            result[name] = var.get()
        for name, entry in com_vars.items():
            result[name] = entry.get()
        for name, widget in video_vars.items():
            val = widget.get()
            result[name] = int(val) if val.isdigit() else val
        root.quit()

    ttk.Button(main_frame, text="Aplicar e Iniciar", command=submit).pack(pady=15, fill="x")

    root.mainloop()
    root.destroy()
    return result
