import customtkinter as ctk
import psutil
import tkinter as tk
from tkinter import ttk

class TaskManagerTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.outer_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.outer_frame.pack(expand=True, padx=20, pady=20, anchor="center")
        self.outer_frame.rowconfigure(0, weight=1)
        self.outer_frame.columnconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Treeview",
            background="#2b2b2b",
            fieldbackground="#2b2b2b",
            foreground="#f5f5f5",
            rowheight=28,
            borderwidth=1,
            relief="solid",
        )
        style.configure(
            "Treeview.Heading",
            background="#1f1f1f",
            foreground="#f5f5f5",
            font=("Arial", 12, "bold")
        )
        style.map(
            "Treeview",
            background=[("selected", "#444444")],
            foreground=[("selected", "#ffffff")]
        )

        # Define colunas
        columns = ("ProcessName", "Id", "Priority", "Memory (MB)")
        self.PRIORITY_MAP = {
            32: "NORMAL",
            64: "IDLE",
            16384: "BELOW_NORMAL",
            32768: "ABOVE_NORMAL",
            128: "HIGH",
            256: "REALTIME"
        }
        self.tree = ttk.Treeview(self.outer_frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="w", stretch=True)

        scrollbar = ttk.Scrollbar(self.outer_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.tree.tag_configure("evenrow", background="#333333")
        self.tree.tag_configure("oddrow", background="#2b2b2b")

        self.update_table()

    def update_table(self):
        if self.winfo_ismapped():
            for item in self.tree.get_children():
                self.tree.delete(item)

            for index, proc in enumerate(psutil.process_iter(["name", "pid", "nice", "memory_info"])):
                name = proc.info.get("name", "")
                if "python" in name.lower():
                    mem = proc.info["memory_info"].rss / (1024 * 1024)
                    pid = proc.info["pid"]
                    nice = proc.info["nice"]
                    priority_name = self.PRIORITY_MAP.get(nice, str(nice))

                    values = (
                        name,
                        pid,
                        priority_name,
                        f"{mem:.2f}",
                    )
                    tag = "evenrow" if index % 2 == 0 else "oddrow"
                    self.tree.insert("", "end", values=values, tags=(tag,))
        self.after(2000, self.update_table)