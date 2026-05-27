import customtkinter as ctk

class TabManager(ctk.CTkFrame):
    """Simple tab manager using CTk buttons."""
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="#171717", corner_radius=8, **kwargs)
        self.grid(row=0, column=0, columnspan=3, sticky="ew", padx=14, pady=(10, 6))
        self.tabs = {}
        self.buttons = {}
        self.left = ctk.CTkFrame(self, fg_color="transparent")
        self.left.pack(side="left", fill="x", expand=True, padx=6, pady=6)
        self.right = ctk.CTkFrame(self, fg_color="transparent")
        self.right.pack(side="right", padx=6, pady=6)
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
            width=118,
            height=34,
            corner_radius=8,
            fg_color="#242424",
            border_width=1,
            border_color="#343434",
            hover_color="#303030",
            text_color="#fff"
        )
        btn.pack(side="left", padx=3)
        self.buttons[name] = btn
        self.tabs[name] = frame
        if frame:
            frame.grid(row=1, column=0, columnspan=3, sticky="nsew")
            frame.lower()
        if self.active is None and frame:
            self.select_tab(name)

    def select_tab(self, name):
        prev = self.active
        if prev == name:
            return

        if prev is not None:
            prev_btn = self.buttons.get(prev)
            if prev_btn:
                prev_btn.configure(
                    fg_color="#242424",
                    border_color="#343434",
                    text_color="#fff"
                )

        new_frame = self.tabs.get(name)
        if new_frame:
            new_frame.tkraise()
        self.active = name

        active_btn = self.buttons.get(name)
        if active_btn:
            active_btn.configure(
                fg_color="#2563eb",
                border_color="#3b82f6",
                text_color="#fff"
            )

        if hasattr(self.master, "on_tab_change"):
            self.master.on_tab_change(prev, name)
