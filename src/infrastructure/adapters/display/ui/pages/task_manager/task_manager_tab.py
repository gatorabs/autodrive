import customtkinter as ctk
import psutil
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class TaskManagerTab(ctk.CTkFrame):
    """Aba de gerenciamento de processos Python com estatísticas de CPU, memória e I/O."""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # quadro interno
        self.outer_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.outer_frame.pack(expand=True, padx=20, pady=20, anchor="center")

        # Configura grid: summary, switch, tabela, métrica, gráfico
        self.outer_frame.rowconfigure((2,4), weight=1)
        self.outer_frame.columnconfigure((0,1), weight=1)

        # 1) Resumo estatístico
        self.summary_label = ctk.CTkLabel(self.outer_frame, text="", anchor="w")
        self.summary_label.grid(row=0, column=0, columnspan=2, sticky="w")

        # 2) Modo compacto
        self.compact_var = ctk.BooleanVar(value=False)
        self.compact_switch = ctk.CTkSwitch(
            self.outer_frame,
            text="Compacto",
            variable=self.compact_var,
            command=self.toggle_compact
        )
        self.compact_switch.grid(row=1, column=0, columnspan=2, sticky="e")

        # Estilo da Treeview
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Treeview",
            background="#2b2b2b",
            fieldbackground="#2b2b2b",
            foreground="#f5f5f5",
            rowheight=28,
            borderwidth=1,
            relief="solid"
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

        # Mapping de prioridade
        self.PRIORITY_MAP = {
            32: "NORMAL",
            64: "IDLE",
            16384: "BELOW_NORMAL",
            32768: "ABOVE_NORMAL",
            128: "HIGH",
            256: "REALTIME"
        }

        # --- TABELA ---
        columns = ("ProcessName", "Id", "Priority", "Memory (MB)")
        self.tree = ttk.Treeview(
            self.outer_frame,
            columns=columns,
            show="headings"
        )
        for col in columns:
            self.tree.heading(
                col,
                text=col,
                command=lambda _col=col: self.sort_by(_col, False)
            )
            self.tree.column(col, anchor="w", stretch=True, minwidth=50)

        # Cores por prioridade
        for prio, color in {
            "REALTIME": "#550000", "HIGH": "#800000",
            "ABOVE_NORMAL": "#aa5500", "BELOW_NORMAL": "#aaaa00",
            "IDLE": "#555500", "NORMAL": "#333333"
        }.items():
            self.tree.tag_configure(prio, background=color)
        self.tree.tag_configure("evenrow", background="#333333")
        self.tree.tag_configure("oddrow", background="#2b2b2b")

        scrollbar = ttk.Scrollbar(
            self.outer_frame,
            orient="vertical",
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=2, column=0, sticky="nsew")
        scrollbar.grid(row=2, column=1, sticky="ns")

        # 3) Seleção de métrica
        self.metric_var = ctk.StringVar(value="Memory")
        self.metric_menu = ctk.CTkOptionMenu(
            self.outer_frame,
            values=["Memory", "CPU", "IO"],
            variable=self.metric_var,
            command=lambda _: self.update_table()
        )
        self.metric_menu.grid(row=3, column=0, sticky="w", pady=(10, 0))

        # --- GRÁFICO ---
        self.fig = Figure(figsize=(5, 2), dpi=100, facecolor="#2b2b2b")
        self.ax = self.fig.add_subplot(111, facecolor="#2b2b2b")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.outer_frame)
        self.canvas.get_tk_widget().grid(
            row=4,
            column=0,
            columnspan=2,
            sticky="nsew",
            pady=(10, 0)
        )

        # Inicia atualização após o frame ser mapeado
        self.after_idle(self.update_table)

    def toggle_compact(self):
        if self.compact_var.get():
            self.metric_menu.grid_remove()
            self.canvas.get_tk_widget().grid_remove()
        else:
            self.metric_menu.grid()
            self.canvas.get_tk_widget().grid()

    def sort_by(self, col, descending):
        data = [(self.tree.set(child, col), child)
                for child in self.tree.get_children('')]
        try:
            data.sort(
                reverse=descending,
                key=lambda t: float(t[0]) if col in ("Id", "Memory (MB)") else t[0].lower()
            )
        except ValueError:
            data.sort(reverse=descending, key=lambda t: t[0].lower())
        for idx, item in enumerate(data):
            self.tree.move(item[1], '', idx)
        self.tree.heading(
            col,
            command=lambda: self.sort_by(col, not descending)
        )

    def update_table(self):
        # Se a aba não estiver visível, apenas reagenda sem atualizar
        if not self.winfo_ismapped():
            self.after(2000, self.update_table)
            return

        # Obtém uso de CPU do sistema (todos os núcleos)
        system_cpu = psutil.cpu_percent(interval=None)
        cores = psutil.cpu_count(logical=True) or 1

        for item in self.tree.get_children():
            self.tree.delete(item)

        labels, mems, cpus, ios = [], [], [], []
        for proc in psutil.process_iter(
            ["name", "pid", "nice", "memory_info", "io_counters"]
        ):
            info = proc.info
            name = info.get("name") or ""
            if "python" in name.lower():
                pid = info["pid"]
                nice = info["nice"]
                prio = self.PRIORITY_MAP.get(nice, str(nice))
                mem = info["memory_info"].rss / (1024 * 1024)
                raw_cpu = proc.cpu_percent(interval=None)
                # Normaliza uso de CPU ao total de núcleos
                cpu = raw_cpu / cores
                io_ct = info.get("io_counters")
                io_sum = ((io_ct.read_bytes + io_ct.write_bytes) / (1024 * 1024)) if io_ct else 0

                labels.append(str(pid))
                mems.append(mem)
                cpus.append(cpu)
                ios.append(io_sum)

                values = (name, pid, prio, f"{mem:.2f}")
                tags = [prio]
                row_tag = "evenrow" if len(labels) % 2 == 0 else "oddrow"
                tags.append(row_tag)
                self.tree.insert("", "end", values=values, tags=tags)

        # Atualiza resumo com uso real de CPU do sistema
        total_mem = sum(mems)
        self.summary_label.configure(
            text=f"Python processes: {len(labels)} | Total RAM: {total_mem:.2f} MB | System CPU: {system_cpu:.1f}%"
        )

        metric = self.metric_var.get()
        if metric == "Memory":
            x_vals, y_vals = mems, labels
            xlabel, title = "MB", "Memória (MB) por Processo"
        elif metric == "CPU":
            x_vals, y_vals = cpus, labels
            xlabel, title = "% CPU (total)", "Uso de CPU (%) por Processo"
        else:
            x_vals, y_vals = ios, labels
            xlabel, title = "I/O (MB)", "I/O (MB) por Processo"

        self.ax.clear()
        self.ax.set_facecolor("#2b2b2b")
        self.fig.patch.set_facecolor("#2b2b2b")
        self.ax.barh(y_vals, x_vals)
        self.ax.set_xlabel(xlabel, color="#f5f5f5")
        self.ax.set_title(title, color="#f5f5f5")
        self.ax.tick_params(axis="x", colors="#f5f5f5")
        self.ax.tick_params(axis="y", colors="#f5f5f5")
        self.fig.tight_layout()
        self.canvas.draw()

        # Agenda próxima atualização
        self.after(2000, self.update_table)