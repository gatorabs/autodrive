import customtkinter as ctk
import math

class SteeringWheel(ctk.CTkFrame):
    """A simple steering wheel widget that emits angle changes."""

    def __init__(self, master, command=None, size=120, **kwargs):
        super().__init__(master, **kwargs)
        self.command = command
        self.size = size
        self.angle = 90
        self._creating = True
        self.canvas = ctk.CTkCanvas(self, width=size, height=size, highlightthickness=0)
        self.canvas.pack()
        self.radius = size / 2 - 10
        self.center = (size / 2, size / 2)
        self.indicator = None
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<Button-1>", self._on_drag)
        self._draw_wheel()
        self._creating = False

    def _draw_wheel(self):
        self.canvas.delete("all")
        x0, y0 = 5, 5
        x1, y1 = self.size - 5, self.size - 5
        wheel_color = "#bfbfbf"
        self.canvas.create_oval(x0, y0, x1, y1, outline=wheel_color, width=2)
        # inner circle for aesthetics
        self.canvas.create_oval(x0 + 15, y0 + 15, x1 - 15, y1 - 15, outline=wheel_color, width=1)
        self._draw_indicator()

    def _draw_indicator(self):
        if self.indicator:
            self.canvas.delete(self.indicator)
        angle_rad = math.radians(self.angle)
        cx, cy = self.center
        x = cx + self.radius * math.cos(angle_rad)
        y = cy - self.radius * math.sin(angle_rad)
        self.indicator = self.canvas.create_line(cx, cy, x, y, fill="orange", width=3)

    def _on_drag(self, event):
        dx = event.x - self.center[0]
        dy = event.y - self.center[1]
        if dx == 0 and dy == 0:
            return
        angle = math.degrees(math.atan2(-dy, dx))
        if angle < 0:
            angle += 360
        if angle > 180:
            angle = 360 - angle
        self.set_angle(angle)

    def set_angle(self, angle, trigger_command=True):
        angle = max(0, min(180, angle))
        self.angle = angle
        self._draw_indicator()
        if not self._creating and trigger_command and self.command:
            self.command(angle)

    def get_angle(self):
        return self.angle
