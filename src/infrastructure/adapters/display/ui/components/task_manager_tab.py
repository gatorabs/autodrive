import customtkinter as ctk
import psutil
import tkinter as tk
from tkinter import ttk

class TaskManagerTab(ctk.CTkFrame):
    """Exibe processos python em uma tabela estilizada."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # Frame interno para centralizar e adicionar margem
        self.outer_frame = ctk.CTkFrame(self, fg_color="transparent")
        # expand=True faz com que a moldura ocupe o espaço disponível; padx/pady adicionam margem
        self.outer_frame.pack(expand=True, padx=20, pady=20, anchor="center")
        # Permitir expansão da Treeview dentro do frame
        self.outer_frame.rowconfigure(0, weight=1)
        self.outer_frame.columnconfigure(0, weight=1)

        # Configura estilo escuro e borda
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Treeview",
            background="#2b2b2b",
            fieldbackground="#2b2b2b",
            foreground="#f5f5f5",
            rowheight=28,
            borderwidth=1,
            relief="solid",              # borda para simular divisórias externas
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
        self.tree = ttk.Treeview(self.outer_frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="w", stretch=True)

        # Barra de rolagem vertical
        scrollbar = ttk.Scrollbar(self.outer_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Posiciona Treeview e scrollbar usando grid para alinhar
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Configura faixas alternadas para dar sensação de linhas divisórias
        self.tree.tag_configure("evenrow", background="#333333")
        self.tree.tag_configure("oddrow", background="#2b2b2b")

        self.update_table()

    def update_table(self):
        """Só atualiza a tabela se o frame estiver visível (ou seja, na aba ativa)."""
        # Se o frame não estiver mapeado, não faz nada agora
        if self.winfo_ismapped():
            # Remove itens antigos
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Percorre processos; insere linhas e aplica tag de faixa
            for index, proc in enumerate(psutil.process_iter(["name", "pid", "nice", "memory_info"])):
                name = proc.info.get("name", "")
                if "python" in name.lower():
                    mem = proc.info["memory_info"].rss / (1024 * 1024)
                    values = (
                        name,
                        proc.info["pid"],
                        proc.info["nice"],
                        f"{mem:.2f}",
                    )
                    tag = "evenrow" if index % 2 == 0 else "oddrow"
                    self.tree.insert("", "end", values=values, tags=(tag,))

        # Agenda próxima atualização (mesmo que invisível, para recarregar logo que ficar visível)
        self.after(2000, self.update_table)
