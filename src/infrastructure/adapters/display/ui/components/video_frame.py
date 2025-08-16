import io
import cv2
import numpy as np
from PIL import Image
import customtkinter as ctk
from customtkinter import CTkImage

from src.infrastructure.constants.ui_constants.component_constants import FRAME_WIDTH_T, FRAME_HEIGHT_T

class VideoFrame(ctk.CTkFrame):
    def __init__(self, master, shared_controls, title="Frame", **kwargs):
        super().__init__(master, **kwargs)
        self.shared_controls = shared_controls
        self.frame_name = title
        self.label = ctk.CTkLabel(self, text=title)
        self.label.pack()

        placeholder_img = Image.new("RGB", (FRAME_WIDTH_T, FRAME_HEIGHT_T), color=(50, 50, 50))
        self.placeholder_ctk_image = CTkImage(light_image=placeholder_img, size=(FRAME_WIDTH_T, FRAME_HEIGHT_T))

        self.image_label = ctk.CTkLabel(self, text="", image=self.placeholder_ctk_image)
        self.image_label.pack()

        self.image_label.bind("<Button-1>", self._open_modal)
        self.modal = None
        self.modal_image_label = None
        self.current_image_full = None

        self.after(500, self._check_flags)

    def update_image(self, frame):
        if self.shared_controls.get("WEBVIEW"):
            self.image_label.configure(image=self.placeholder_ctk_image, text="Webview ATIVO.")
            self.image_label.image = self.placeholder_ctk_image
            self.current_image_full = None
            self._close_modal()
            return
        if (self.shared_controls.get("SAFE_STOP") and self.frame_name in ("NORMAL_FRAME", "EDGES_FRAME") or
                self.shared_controls.get("OBJ_SAFE_STOP") and self.frame_name == "OBJECT_FRAME"):
            self.image_label.configure(image=self.placeholder_ctk_image, text="Erro na transmissão.")
            self.image_label.image = self.placeholder_ctk_image
            self.current_image_full = None
            self._close_modal()
            return
        if self.modal and self.modal.winfo_exists():
            if frame is not None:
                image = self._to_pil_image(frame)
                if image:
                    self.current_image_full = image
                    modal_img = CTkImage(light_image=image, size=image.size)
                    self.modal_image_label.configure(image=modal_img)
                    self.modal_image_label.image = modal_img
            return
        if frame is not None:
            image = self._to_pil_image(frame)
            if image:
                self.current_image_full = image
                resized = image.resize((FRAME_WIDTH_T, FRAME_HEIGHT_T))
                ctk_image = CTkImage(light_image=resized, size=(FRAME_WIDTH_T, FRAME_HEIGHT_T))
                self.image_label.configure(image=ctk_image, text="")
                self.image_label.image = ctk_image

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
        modal_img = CTkImage(light_image=self.current_image_full, size=self.current_image_full.size)
        self.modal_image_label = ctk.CTkLabel(self.modal, text="", image=modal_img)
        self.modal_image_label.pack()
        self.modal_image_label.image = modal_img
        self.image_label.configure(image=self.placeholder_ctk_image, text="")
        self.image_label.image = self.placeholder_ctk_image

    def _close_modal(self):
        if self.modal and self.modal.winfo_exists():
            self.modal.destroy()
        self.modal = None
        self.modal_image_label = None
        if self.current_image_full:
            resized = self.current_image_full.resize((FRAME_WIDTH_T, FRAME_HEIGHT_T))
            ctk_image = CTkImage(light_image=resized, size=(FRAME_WIDTH_T, FRAME_HEIGHT_T))
            self.image_label.configure(image=ctk_image, text="")
            self.image_label.image = ctk_image

    def _check_flags(self):
        if self.shared_controls.get("WEBVIEW"):
            self.image_label.configure(image=self.placeholder_ctk_image, text="Webview ATIVO.")
            self.image_label.image = self.placeholder_ctk_image
            self.current_image_full = None
            self._close_modal()
        elif self.shared_controls.get("SAFE_STOP") and self.frame_name in ("NORMAL_FRAME", "EDGES_FRAME"):
            self.image_label.configure(image=self.placeholder_ctk_image, text="Erro na transmissão.")
            self.image_label.image = self.placeholder_ctk_image
            self.current_image_full = None
            self._close_modal()
        self.after(200, self._check_flags)
