import tkinter as tk
from tkinter import ttk
from utils.constants import flags

def setup_flag_interface():
    root = tk.Tk()
    root.title("Configure Shared Controls")
    root.geometry("400x300")

    style = ttk.Style()
    style.configure("TButton", font=("Arial", 10))
    style.configure("TCheckbutton", font=("Arial", 10))
    style.configure("TLabel", font=("Arial", 10))

    main_frame = ttk.Frame(root, padding=10)
    main_frame.pack(fill="both", expand=True)

    com_defaults = {"SECURITY_COM": "COM5", "SENDER_COM": "COM3"}

    bool_vars = {}
    com_vars = {}

    flags_frame = ttk.LabelFrame(main_frame, text="Opções de Controle", padding=(10, 5))
    flags_frame.pack(fill="x", padx=5, pady=10)

    for name, default in flags.items():
        var = tk.BooleanVar(value=default)
        chk = ttk.Checkbutton(flags_frame, text=name, variable=var)
        chk.pack(anchor="w", pady=2)
        bool_vars[name] = var

    com_frame = ttk.LabelFrame(main_frame, text="Portas de Comunicação", padding=(10, 5))
    com_frame.pack(fill="x", padx=5, pady=10)

    for name, default in com_defaults.items():
        row = ttk.Frame(com_frame)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=name, width=14).pack(side="left")
        entry = ttk.Entry(row)
        entry.insert(0, default)
        entry.pack(side="left", fill="x", expand=True)
        com_vars[name] = entry

    result = {}

    def submit():
        for name, var in bool_vars.items():
            result[name] = var.get()
        for name, entry in com_vars.items():
            result[name] = entry.get()
        root.quit()

    submit_btn = ttk.Button(main_frame, text="Aplicar e Iniciar", command=submit)
    submit_btn.pack(pady=15, fill="x")

    root.mainloop()
    root.destroy()

    return result
