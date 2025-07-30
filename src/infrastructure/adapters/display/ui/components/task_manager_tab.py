import customtkinter as ctk
import psutil
import tkinter as tk
from tkinter import ttk

class TaskManagerTab(ctk.CTkFrame):
    """Exibe os processos python em um Treeview."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # Configura o estilo do Treeview para combinar com o tema do CustomTkinter
        style = ttk.Style()
        style.theme_use("default")
        # Cores básicas (podem ser ajustadas conforme necessário)
        style.configure(
            "Treeview",
            background="#2b2b2b",         # cor de fundo das células
            fieldbackground="#2b2b2b",
            foreground="#f5f5f5",         # cor do texto
            rowheight=24                  # altura das linhas
        )
        style.configure(
            "Treeview.Heading",
            background="#1f1f1f",         # cor de fundo do cabeçalho
            foreground="#f5f5f5",
            font=("Arial", 12, "bold")
        )
        style.map(
            "Treeview",
            background=[("selected", "#444444")],
            foreground=[("selected", "#ffffff")]
        )

        # Define as colunas da tabela
        columns = ("ProcessName", "Id", "Priority", "Memory (MB)")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="w", stretch=True)

        # Adiciona uma barra de rolagem vertical ao Treeview
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Carrega os dados iniciais
        self.update_table()

    def update_table(self):
        """Atualiza o conteúdo do Treeview com processos python atuais."""
        # Remove entradas antigas
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Percorre os processos e adiciona linhas apenas para executáveis python
        for proc in psutil.process_iter(["name", "pid", "nice", "memory_info"]):
            name = proc.info.get("name", "")
            if "python" in name.lower():
                mem = proc.info["memory_info"].rss / (1024 * 1024)  # MB
                values = (
                    name,
                    proc.info["pid"],
                    proc.info["nice"],
                    f"{mem:.2f}",
                )
                self.tree.insert("", "end", values=values)

        # Agenda nova atualização
        self.after(2000, self.update_table)
