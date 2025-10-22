import io

import cv2
import numpy as np
from PIL import Image
import customtkinter as ctk
from customtkinter import CTkImage

from src.infrastructure.constants.ui_constants.component_constants import (
    FRAME_HEIGHT_T,
    FRAME_WIDTH_T,
)


class VideoFrame(ctk.CTkFrame):
    def __init__(self, master, shared_controls, title="Frame", **kwargs):
        super().__init__(master, **kwargs)
        self.shared_controls = shared_controls
        self.frame_name = title

        self.label = ctk.CTkLabel(self, text=title)
        self.label.pack()

        placeholder_img = Image.new(
            "RGB", (FRAME_WIDTH_T, FRAME_HEIGHT_T), color=(50, 50, 50)
        )
        self.placeholder_ctk_image = CTkImage(
            light_image=placeholder_img, size=(FRAME_WIDTH_T, FRAME_HEIGHT_T)
        )

        self.image_label = ctk.CTkLabel(
            self, text="", image=self.placeholder_ctk_image
        )
        self.image_label.pack()

        self.image_label.bind("<Button-1>", self._open_modal)
        self.modal = None
        self.modal_image_label = None
        self.current_image_full = None

        self.after(500, self._check_flags)

    def update_image(self, frame):
        placeholder_message = self._placeholder_message()
        if placeholder_message:
            self._show_placeholder(placeholder_message)
            return

        if frame is None:
            return

        image = self._to_pil_image(frame)
        if image is None:
            return

        self.current_image_full = image

        if self.modal and self.modal.winfo_exists():
            self._update_modal_image(image)
            return

        self._update_main_image(image)

    def _to_pil_image(self, frame):
        if isinstance(frame, (bytes, bytearray)):
            return Image.open(io.BytesIO(frame))
        if isinstance(frame, np.ndarray):
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return Image.fromarray(rgb)
        return None

    def _open_modal(self, _event=None):
        if self.current_image_full is None:
            return
        if self.modal and self.modal.winfo_exists():
            return

        self.modal = ctk.CTkToplevel(self)
        self.modal.title(self.label.cget("text"))
        self.modal.transient(self.winfo_toplevel())
        self.modal.resizable(False, False)
        self.modal.protocol("WM_DELETE_WINDOW", self._close_modal)

        modal_img = CTkImage(
            light_image=self.current_image_full, size=self.current_image_full.size
        )
        self.modal_image_label = ctk.CTkLabel(self.modal, text="", image=modal_img)
        self.modal_image_label.pack()
        self.modal_image_label.image = modal_img
        self._set_main_image(self.placeholder_ctk_image, "")

    def _close_modal(self):
        if self.modal and self.modal.winfo_exists():
            self.modal.destroy()
        self.modal = None
        self.modal_image_label = None
        if self.current_image_full:
            self._update_main_image(self.current_image_full)

    def _check_flags(self):
        placeholder_message = self._placeholder_message()
        if placeholder_message:
            self._show_placeholder(placeholder_message)
        self.after(200, self._check_flags)

    def _placeholder_message(self):
        if self.shared_controls.get("WEBVIEW"):
            return "Webview ATIVO."

        safe_stop = self.shared_controls.get("SAFE_STOP") and self.frame_name in (
            "NORMAL_FRAME",
            "EDGES_FRAME",
        )
        obj_safe_stop = (
            self.shared_controls.get("OBJ_SAFE_STOP")
            and self.frame_name == "OBJECT_FRAME"
        )

        if safe_stop or obj_safe_stop:
            return "Erro na transmissão."

        return None

    def _show_placeholder(self, message: str) -> None:
        self.current_image_full = None
        self._set_main_image(self.placeholder_ctk_image, message)
        self._close_modal()

    def _set_main_image(self, ctk_image: CTkImage, text: str) -> None:
        self.image_label.configure(image=ctk_image, text=text)
        self.image_label.image = ctk_image

    def _update_main_image(self, image: Image.Image) -> None:
        resized = image.resize((FRAME_WIDTH_T, FRAME_HEIGHT_T))
        ctk_image = CTkImage(light_image=resized, size=(FRAME_WIDTH_T, FRAME_HEIGHT_T))
        self._set_main_image(ctk_image, "")

    def _update_modal_image(self, image: Image.Image) -> None:
        if not self.modal_image_label:
            return
        modal_img = CTkImage(light_image=image, size=image.size)
        self.modal_image_label.configure(image=modal_img)
        self.modal_image_label.image = modal_img
