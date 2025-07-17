from tkinter import ttk
import tkinter as tk

def create_trackbar_row(parent, label_text, var, from_, to, resolution=None):
    row = ttk.Frame(parent)
    row.pack(fill="x", pady=2)
    ttk.Label(row, text=label_text, width=8).pack(side="left")
    scale = ttk.Scale(row, from_=from_, to=to, orient="horizontal", variable=var)
    if resolution:
        scale.configure(length=200)
    scale.pack(side="left", fill="x", expand=True)
    value_label = ttk.Label(row, text=str(var.get()), width=6)
    value_label.pack(side="left", padx=5)
    var.trace_add("write", lambda *args: value_label.config(
        text=f"{var.get():.3f}" if isinstance(var.get(), float) else str(var.get())
    ))

def create_trackbar_var(tk_controls, key, var_type="int"):
    if var_type == "float":
        var = tk.DoubleVar(value=tk_controls.get(key, 0.0))
    else:
        var = tk.IntVar(value=tk_controls.get(key, 0))
    var.trace_add("write", lambda *args: tk_controls.__setitem__(key, var.get()))
    return var

def create_section(main_frame, title, row, col, colspan=1):
    frame = ttk.LabelFrame(main_frame, text=title, padding=(10, 5))
    frame.grid(row=row, column=col, columnspan=colspan, padx=5, pady=5, sticky="nsew")
    return frame