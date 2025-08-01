import customtkinter as ctk

class TabManager(ctk.CTkFrame):
    """Simple tab manager using CTk buttons."""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid(row=0, column=0, columnspan=3, sticky="ew", padx=10, pady=(5,0))
        self.tabs, self.buttons = {}, {}
        self.left = ctk.CTkFrame(self, fg_color="transparent")
        self.left.pack(side="left", fill="x", expand=True)
        self.right = ctk.CTkFrame(self, fg_color="transparent")
        self.right.pack(side="right")
        self.active = None

    def create_tab(self, name, frame, on_right=False, on_select=None):
        def cb():
            if on_select:
                on_select(name)
            else:
                self.select_tab(name)

        btn = ctk.CTkButton(
            self.right if on_right else self.left,
            text=name,
            command=cb,
            width=80, height=28,
            fg_color="transparent",
            hover_color="#444444",
            text_color="#fff"
        )
        btn.pack(side="left", padx=5)
        self.buttons[name] = btn
        self.tabs[name] = frame
        if frame:
            frame.grid_forget()
        if self.active is None and frame:
            self.select_tab(name)

    def select_tab(self, name):
        prev_name = self.active
        if self.active:
            prev = self.tabs.get(self.active)
            if prev:
                prev.grid_forget()

        frm = self.tabs.get(name)
        if frm:
            frm.grid(row=1, column=0, columnspan=3, sticky="nsew")
            self.active = name

        if hasattr(self.master, "on_tab_change"):
            self.master.on_tab_change(prev_name, name)
