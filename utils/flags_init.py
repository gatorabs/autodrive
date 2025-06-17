import tkinter as tk
from tkinter import ttk
from utils.constants import flags


def setup_flag_interface():
    root = tk.Tk()
    root.title("Configure Shared Controls")
    root.geometry("400x400")

    com_defaults = {"SECURITY_COM": "COM5", "SENDER_COM": "COM3"}

    bool_vars = {}
    com_vars = {}
    row = 0

    for name, default in flags.items():
        var = tk.BooleanVar(value=default)
        chk = ttk.Checkbutton(root, text=name, variable=var)
        chk.grid(row=row, column=0, sticky="w", padx=10, pady=5)
        bool_vars[name] = var
        row += 1

    for name, default in com_defaults.items():
        lbl = ttk.Label(root, text=name)
        lbl.grid(row=row, column=0, sticky="w", padx=10, pady=5)
        entry = ttk.Entry(root)
        entry.insert(0, default)
        entry.grid(row=row, column=1, padx=10, pady=5)
        com_vars[name] = entry
        row += 1

    result = {}

    def submit():
        for name, var in bool_vars.items():
            result[name] = var.get()
        for name, entry in com_vars.items():
            result[name] = entry.get()
        root.quit()

    submit_btn = ttk.Button(root, text="Apply and Launch", command=submit)
    submit_btn.grid(row=row, column=0, columnspan=2, pady=20)

    root.mainloop()
    root.destroy()

    return result