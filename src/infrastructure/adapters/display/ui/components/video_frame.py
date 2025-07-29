import io
from PIL import Image
import customtkinter as ctk
from customtkinter import CTkImage

from src.infrastructure.adapters.display.ui.constants import FRAME_WIDTH_T, FRAME_HEIGHT_T

class VideoFrame(ctk.CTkFrame):
    """Container for displaying a video frame."""

    def __init__(self, master, shared_controls, title="Frame", **kwargs):
        super().__init__(master, **kwargs)
        self.shared_controls = shared_controls
        self.label = ctk.CTkLabel(self, text=title)
        self.label.pack()

        placeholder_img = Image.new("RGB", (FRAME_WIDTH_T, FRAME_HEIGHT_T), color=(50, 50, 50))
        self.placeholder_ctk_image = CTkImage(light_image=placeholder_img, size=(FRAME_WIDTH_T, FRAME_HEIGHT_T))

        self.image_label = ctk.CTkLabel(self, text="", image=self.placeholder_ctk_image)
        self.image_label.pack()

    def update_image(self, image_bytes):
        if self.shared_controls.get("WEBVIEW"):
            self.image_label.configure(image=self.placeholder_ctk_image, text="Webview ATIVO.")
            self.image_label.image = self.placeholder_ctk_image
            return
        if image_bytes:
            image = Image.open(io.BytesIO(image_bytes)).resize((FRAME_WIDTH_T, FRAME_HEIGHT_T))
            ctk_image = CTkImage(light_image=image, size=(FRAME_WIDTH_T, FRAME_HEIGHT_T))
            self.image_label.configure(image=ctk_image, text="")
            self.image_label.image = ctk_image
