import tkinter as tk

class RoundedProgressbar(tk.Canvas):
    def __init__(self, parent, width=300, height=20, corner_radius=10, max_value=100, **kwargs):
        super().__init__(parent, width=width, height=height, bg="white", highlightthickness=0, **kwargs)
        self.width = width
        self.height = height
        self.corner_radius = corner_radius
        self.max_value = max_value
        self.progress_value = 0

        self.bg_color = "#ddd"
        self.fg_color = "#0078d7"  # azul

        self.draw_background()
        self.draw_progress()

    def draw_rounded_rect(self, x1, y1, x2, y2, r, color):
        self.create_arc(x1, y1, x1+2*r, y1+2*r, start=90, extent=90, fill=color, outline=color)
        self.create_arc(x2-2*r, y1, x2, y1+2*r, start=0, extent=90, fill=color, outline=color)
        self.create_arc(x1, y2-2*r, x1+2*r, y2, start=180, extent=90, fill=color, outline=color)
        self.create_arc(x2-2*r, y2-2*r, x2, y2, start=270, extent=90, fill=color, outline=color)
        self.create_rectangle(x1+r, y1, x2-r, y2, fill=color, outline=color)
        self.create_rectangle(x1, y1+r, x2, y2-r, fill=color, outline=color)

    def draw_background(self):
        self.delete("background")
        self.draw_rounded_rect(0, 0, self.width, self.height, self.corner_radius, self.bg_color)

    def draw_progress(self):
        self.delete("progress")
        progress_width = (self.progress_value / self.max_value) * self.width
        if progress_width < self.corner_radius:
            # preencher com um círculo parcial para manter arredondado
            self.create_arc(0, 0, 2*self.corner_radius, self.height, start=90, extent=180, fill=self.fg_color, outline="", tags="progress")
        else:
            self.draw_rounded_rect(0, 0, progress_width, self.height, self.corner_radius, self.fg_color)
        self.update_idletasks()

    def set_value(self, value):
        self.progress_value = max(0, min(value, self.max_value))
        self.draw_progress()
