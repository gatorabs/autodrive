from __future__ import annotations

import queue
import sys
import threading
from pathlib import Path
from tkinter import messagebox

import cv2
import customtkinter as ctk
from PIL import Image

if __package__ in (None, "", "app"):
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from services.capture_service import CameraCaptureSession, CaptureTarget, slugify  # type: ignore
    from services.dataset_service import DatasetInventory, discover_datasets  # type: ignore
    from services.model_registry_service import discover_trained_models, promote_model  # type: ignore
    from services.training_service import TrainingRequest, run_training  # type: ignore
else:
    from ..services.capture_service import CameraCaptureSession, CaptureTarget, slugify
    from ..services.dataset_service import DatasetInventory, discover_datasets
    from ..services.model_registry_service import discover_trained_models, promote_model
    from ..services.training_service import TrainingRequest, run_training


TRAINER_DIR = Path(__file__).resolve().parents[1]
DATASET_DIR = TRAINER_DIR / "dataset"


class ModelTrainerApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Autodrive Model Trainer")
        self.geometry("1180x760")
        self.minsize(980, 640)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.datasets: list[DatasetInventory] = []
        self.log_queue: queue.Queue[str] = queue.Queue()
        self.training_thread: threading.Thread | None = None
        self.selected_model_path: Path | None = None
        self.capture_session: CameraCaptureSession | None = None
        self.capture_job: str | None = None
        self.capture_image = None
        self.capture_frame_shape: tuple[int, int] | None = None
        self.capture_render = {"x": 0, "y": 0, "width": 1, "height": 1, "scale": 1.0}
        self.drag_start: tuple[int, int] | None = None

        self.base_model_var = ctk.StringVar(value="yolov8n.pt")
        self.epochs_var = ctk.StringVar(value="50")
        self.imgsz_var = ctk.StringVar(value="640")
        self.batch_var = ctk.StringVar(value="8")
        self.device_var = ctk.StringVar(value="auto")
        self.val_ratio_var = ctk.StringVar(value="0.2")
        self.seed_var = ctk.StringVar(value="42")
        self.camera_var = ctk.StringVar(value="0")
        self.capture_class_var = ctk.StringVar(value="PLACA_PARE")
        self.capture_class_id_var = ctk.StringVar(value="0")
        self.capture_fps_var = ctk.StringVar(value="2.0")
        self.capture_status_var = ctk.StringVar(value="Camera closed")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self._build_header()
        self._build_body()
        self.refresh_datasets()
        self.refresh_models()
        self.after(120, self._drain_logs)

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text="Autodrive Model Trainer",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title.grid(row=0, column=0, padx=24, pady=(18, 2), sticky="w")

        subtitle = ctk.CTkLabel(
            header,
            text="Train the composed YOLO model and choose which custom weight the car loads.",
            text_color="#A7B4CC",
        )
        subtitle.grid(row=1, column=0, padx=24, pady=(0, 18), sticky="w")

        refresh = ctk.CTkButton(header, text="Refresh", command=self.refresh_all, width=140)
        refresh.grid(row=0, column=1, rowspan=2, padx=24, pady=18, sticky="e")

    def _build_body(self) -> None:
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, padx=18, pady=18, sticky="nsew")
        body.grid_columnconfigure((0, 1, 2), weight=1, uniform="cols")
        body.grid_rowconfigure(0, weight=2)
        body.grid_rowconfigure(1, weight=1)

        self.capture_panel = self._card(body, "Capture Images")
        self.capture_panel.grid(row=0, column=0, columnspan=3, padx=8, pady=(0, 14), sticky="nsew")

        self.dataset_panel = self._card(body, "Datasets")
        self.dataset_panel.grid(row=1, column=0, padx=8, sticky="nsew")

        self.training_panel = self._card(body, "Training")
        self.training_panel.grid(row=1, column=1, padx=8, sticky="nsew")

        self.models_panel = self._card(body, "Models")
        self.models_panel.grid(row=1, column=2, padx=8, sticky="nsew")

        self._build_capture_panel()
        self._build_dataset_panel()
        self._build_training_panel()
        self._build_models_panel()

    def _card(self, parent: ctk.CTkFrame, title: str) -> ctk.CTkFrame:
        card = ctk.CTkFrame(parent, corner_radius=14, border_width=1, border_color="#26344D")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)
        label = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=17, weight="bold"))
        label.grid(row=0, column=0, padx=18, pady=(16, 10), sticky="w")
        return card

    def _build_capture_panel(self) -> None:
        content = ctk.CTkFrame(self.capture_panel, fg_color="transparent")
        content.grid(row=1, column=0, padx=18, pady=(0, 18), sticky="nsew")
        content.grid_columnconfigure(0, weight=3)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(0, weight=1)

        self.capture_preview = ctk.CTkLabel(
            content,
            text="Open the camera, then drag on this preview to draw a bounding box.",
            fg_color="#0B1220",
            corner_radius=12,
        )
        self.capture_preview.grid(row=0, column=0, padx=(0, 16), sticky="nsew")
        self.capture_preview.bind("<ButtonPress-1>", self._on_capture_press)
        self.capture_preview.bind("<B1-Motion>", self._on_capture_drag)
        self.capture_preview.bind("<ButtonRelease-1>", self._on_capture_release)

        controls = ctk.CTkFrame(content, fg_color="transparent")
        controls.grid(row=0, column=1, sticky="nsew")
        controls.grid_columnconfigure(1, weight=1)

        fields = [
            ("Camera", self.camera_var),
            ("Class name", self.capture_class_var),
            ("Class ID", self.capture_class_id_var),
            ("Auto FPS", self.capture_fps_var),
        ]
        for row, (label, var) in enumerate(fields):
            ctk.CTkLabel(controls, text=label).grid(row=row, column=0, padx=(0, 10), pady=5, sticky="w")
            ctk.CTkEntry(controls, textvariable=var).grid(row=row, column=1, pady=5, sticky="ew")

        actions = ctk.CTkFrame(controls, fg_color="transparent")
        actions.grid(row=len(fields), column=0, columnspan=2, pady=(10, 8), sticky="ew")
        actions.grid_columnconfigure((0, 1), weight=1)

        buttons = [
            ("Open camera", self.open_capture_camera),
            ("Close camera", self.close_capture_camera),
            ("Start tracking", self.start_capture_tracking),
            ("Stop tracking", self.stop_capture_tracking),
            ("Save frame", self.save_capture_frame),
            ("Toggle recording", self.toggle_capture_recording),
            ("Clear bbox", self.clear_capture_bbox),
            ("Refresh datasets", self.refresh_datasets),
        ]
        for index, (text, command) in enumerate(buttons):
            ctk.CTkButton(actions, text=text, command=command).grid(
                row=index // 2,
                column=index % 2,
                padx=(0, 6) if index % 2 == 0 else (6, 0),
                pady=4,
                sticky="ew",
            )

        ctk.CTkLabel(
            controls,
            textvariable=self.capture_status_var,
            text_color="#A7B4CC",
            justify="left",
            wraplength=260,
        ).grid(row=len(fields) + 1, column=0, columnspan=2, pady=(10, 0), sticky="ew")

    def _build_dataset_panel(self) -> None:
        self.dataset_list = ctk.CTkScrollableFrame(self.dataset_panel, fg_color="transparent")
        self.dataset_list.grid(row=1, column=0, padx=14, pady=(0, 14), sticky="nsew")

    def _build_training_panel(self) -> None:
        form = ctk.CTkFrame(self.training_panel, fg_color="transparent")
        form.grid(row=1, column=0, padx=18, pady=(0, 8), sticky="nsew")
        form.grid_columnconfigure(1, weight=1)

        fields = [
            ("Base model", self.base_model_var),
            ("Epochs", self.epochs_var),
            ("Image size", self.imgsz_var),
            ("Batch", self.batch_var),
            ("Device", self.device_var),
            ("Validation ratio", self.val_ratio_var),
            ("Seed", self.seed_var),
        ]
        for row, (label, var) in enumerate(fields):
            ctk.CTkLabel(form, text=label).grid(row=row, column=0, padx=(0, 10), pady=5, sticky="w")
            ctk.CTkEntry(form, textvariable=var).grid(row=row, column=1, pady=5, sticky="ew")

        actions = ctk.CTkFrame(form, fg_color="transparent")
        actions.grid(row=len(fields), column=0, columnspan=2, pady=(12, 8), sticky="ew")
        actions.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(actions, text="Prepare only", command=lambda: self.start_training(True)).grid(
            row=0, column=0, padx=(0, 6), sticky="ew"
        )
        ctk.CTkButton(actions, text="Train composed model", command=lambda: self.start_training(False)).grid(
            row=0, column=1, padx=(6, 0), sticky="ew"
        )

        self.log_box = ctk.CTkTextbox(form, height=240, wrap="word")
        self.log_box.grid(row=len(fields) + 1, column=0, columnspan=2, sticky="nsew")
        form.grid_rowconfigure(len(fields) + 1, weight=1)

    def _build_models_panel(self) -> None:
        self.models_list = ctk.CTkScrollableFrame(self.models_panel, fg_color="transparent")
        self.models_list.grid(row=1, column=0, padx=14, pady=(0, 8), sticky="nsew")

        actions = ctk.CTkFrame(self.models_panel, fg_color="transparent")
        actions.grid(row=2, column=0, padx=14, pady=(0, 14), sticky="ew")
        actions.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(actions, text="Promote as active", command=self.promote_selected_model).grid(
            row=0, column=0, padx=(0, 6), sticky="ew"
        )
        ctk.CTkButton(actions, text="Refresh models", command=self.refresh_models).grid(
            row=0, column=1, padx=(6, 0), sticky="ew"
        )

    def refresh_all(self) -> None:
        self.refresh_datasets()
        self.refresh_models()

    def open_capture_camera(self) -> None:
        self.close_capture_camera()
        try:
            camera_index = int(self.camera_var.get())
            class_id = int(self.capture_class_id_var.get())
            target_fps = float(self.capture_fps_var.get())
        except ValueError as exc:
            messagebox.showerror("Invalid capture parameter", str(exc))
            return

        class_name = self.capture_class_var.get().strip() or "objeto"
        folder_name = slugify(class_name, f"class_{class_id:02d}")
        target = CaptureTarget(
            class_name=class_name,
            class_id=class_id,
            root=DATASET_DIR / folder_name,
        )
        session = CameraCaptureSession(
            camera_index=camera_index,
            target=target,
            target_fps=target_fps,
        )
        try:
            session.open()
        except Exception as exc:
            messagebox.showerror("Camera unavailable", str(exc))
            return

        self.capture_session = session
        self.capture_status_var.set(f"Camera {camera_index} opened | saving to {target.root}")
        self._schedule_capture_preview()

    def close_capture_camera(self) -> None:
        if self.capture_job is not None:
            self.after_cancel(self.capture_job)
            self.capture_job = None
        if self.capture_session is not None:
            self.capture_session.close()
            self.capture_session = None
        self.capture_status_var.set("Camera closed")

    def start_capture_tracking(self) -> None:
        if self.capture_session is None:
            messagebox.showwarning("Camera closed", "Open the camera before starting tracking.")
            return
        try:
            self.capture_session.start_tracking()
        except Exception as exc:
            messagebox.showwarning("Bounding box required", str(exc))
        self._update_capture_status()

    def stop_capture_tracking(self) -> None:
        if self.capture_session is not None:
            self.capture_session.stop_tracking()
        self._update_capture_status()

    def toggle_capture_recording(self) -> None:
        if self.capture_session is None:
            messagebox.showwarning("Camera closed", "Open the camera before recording.")
            return
        self.capture_session.set_recording(not self.capture_session.recording)
        self._update_capture_status()

    def save_capture_frame(self) -> None:
        if self.capture_session is None:
            messagebox.showwarning("Camera closed", "Open the camera before saving frames.")
            return
        saved = self.capture_session.save_current_frame()
        if saved is None:
            messagebox.showwarning("No frame", "No camera frame is available yet.")
            return
        self.refresh_datasets()
        self._update_capture_status()

    def clear_capture_bbox(self) -> None:
        if self.capture_session is not None:
            self.capture_session.clear_bbox()
        self._update_capture_status()

    def _schedule_capture_preview(self) -> None:
        self.capture_job = self.after(30, self._update_capture_preview)

    def _update_capture_preview(self) -> None:
        if self.capture_session is None:
            self.capture_job = None
            return

        frame = self.capture_session.read()
        if frame is not None:
            overlay = self.capture_session.draw_overlay(frame)
            self._render_capture_frame(overlay)
        self._update_capture_status()
        self._schedule_capture_preview()

    def _render_capture_frame(self, frame) -> None:
        frame_height, frame_width = frame.shape[:2]
        self.capture_frame_shape = (frame_height, frame_width)

        label_width = max(320, self.capture_preview.winfo_width())
        label_height = max(220, self.capture_preview.winfo_height())
        scale = min(label_width / frame_width, label_height / frame_height)
        render_width = max(1, int(frame_width * scale))
        render_height = max(1, int(frame_height * scale))
        origin_x = max(0, (label_width - render_width) // 2)
        origin_y = max(0, (label_height - render_height) // 2)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb).resize((render_width, render_height), Image.Resampling.LANCZOS)
        self.capture_image = ctk.CTkImage(light_image=image, dark_image=image, size=(render_width, render_height))
        self.capture_preview.configure(image=self.capture_image, text="")
        self.capture_render = {
            "x": origin_x,
            "y": origin_y,
            "width": render_width,
            "height": render_height,
            "scale": scale,
        }

    def _update_capture_status(self) -> None:
        if self.capture_session is None:
            return
        session = self.capture_session
        self.capture_status_var.set(
            f"{session.status}\n"
            f"Tracking: {'on' if session.tracking else 'off'} | "
            f"Recording: {'on' if session.recording else 'off'} | "
            f"Saved: {session.saved_count}"
        )

    def _preview_to_frame_point(self, x: int, y: int) -> tuple[int, int] | None:
        if self.capture_frame_shape is None:
            return None
        frame_height, frame_width = self.capture_frame_shape
        render = self.capture_render
        local_x = x - int(render["x"])
        local_y = y - int(render["y"])
        if local_x < 0 or local_y < 0 or local_x > render["width"] or local_y > render["height"]:
            return None
        scale = float(render["scale"])
        return (
            max(0, min(frame_width - 1, int(local_x / scale))),
            max(0, min(frame_height - 1, int(local_y / scale))),
        )

    def _on_capture_press(self, event) -> None:
        if self.capture_session is None:
            return
        point = self._preview_to_frame_point(event.x, event.y)
        self.drag_start = point

    def _on_capture_drag(self, event) -> None:
        self._update_drag_bbox(event.x, event.y)

    def _on_capture_release(self, event) -> None:
        self._update_drag_bbox(event.x, event.y)
        self.drag_start = None
        self._update_capture_status()

    def _update_drag_bbox(self, x: int, y: int) -> None:
        if self.capture_session is None or self.drag_start is None:
            return
        point = self._preview_to_frame_point(x, y)
        if point is None:
            return
        x1, y1 = self.drag_start
        x2, y2 = point
        left, right = sorted((x1, x2))
        top, bottom = sorted((y1, y2))
        if right - left < 2 or bottom - top < 2:
            return
        self.capture_session.set_bbox((left, top, right - left, bottom - top))

    def refresh_datasets(self) -> None:
        self.datasets = discover_datasets(DATASET_DIR)
        for child in self.dataset_list.winfo_children():
            child.destroy()

        if not self.datasets:
            ctk.CTkLabel(
                self.dataset_list,
                text=f"No datasets found in {DATASET_DIR}",
                text_color="#FCA5A5",
            ).pack(anchor="w", pady=8)
            return

        for item in self.datasets:
            color = "#86EFAC" if item.is_valid else "#FCA5A5"
            text = (
                f"{item.class_name}\n"
                f"{item.paired_count} pairs | {item.image_count} images | {item.label_count} labels\n"
                f"class ids: {', '.join(str(value) for value in item.class_ids)}"
            )
            if item.images_without_labels or item.labels_without_images:
                text += (
                    f"\nmissing labels: {item.images_without_labels} | "
                    f"orphan labels: {item.labels_without_images}"
                )
            label = ctk.CTkLabel(
                self.dataset_list,
                text=text,
                justify="left",
                anchor="w",
                text_color=color,
            )
            label.pack(fill="x", padx=2, pady=8)

    def refresh_models(self) -> None:
        for child in self.models_list.winfo_children():
            child.destroy()

        models = discover_trained_models()
        if not models:
            ctk.CTkLabel(
                self.models_list,
                text="No trained models found under yolo_runs.",
                text_color="#FCA5A5",
            ).pack(anchor="w", pady=8)
            return

        for model in models:
            classes = ", ".join(model.classes) if model.classes else "classes unavailable"
            button = ctk.CTkButton(
                self.models_list,
                text=f"{model.name}\n{classes}\n{model.path}",
                anchor="w",
                height=82,
                fg_color="#1F2937",
                hover_color="#2B3A55",
                command=lambda path=model.path: self.select_model(path),
            )
            button.pack(fill="x", pady=6)

    def select_model(self, path: Path) -> None:
        self.selected_model_path = path
        self._log(f"Selected model: {path}")

    def promote_selected_model(self) -> None:
        if self.selected_model_path is None:
            messagebox.showwarning("No model selected", "Select a model before promoting it.")
            return
        try:
            registry_path = promote_model(self.selected_model_path)
        except Exception as exc:
            messagebox.showerror("Promotion failed", str(exc))
            return
        messagebox.showinfo("Active model updated", f"Registry updated:\n{registry_path}")
        self._log(f"Active model registry updated: {registry_path}")

    def start_training(self, prepare_only: bool) -> None:
        if self.training_thread and self.training_thread.is_alive():
            messagebox.showwarning("Training running", "Wait for the current training to finish.")
            return

        valid_datasets = [item for item in self.datasets if item.is_valid]
        if not valid_datasets:
            messagebox.showerror("Invalid dataset", "No valid dataset with image/label pairs was found.")
            return

        try:
            request = TrainingRequest(
                datasets=valid_datasets,
                base_model=self.base_model_var.get().strip() or "yolov8n.pt",
                epochs=int(self.epochs_var.get()),
                image_size=int(self.imgsz_var.get()),
                batch=int(self.batch_var.get()),
                device=self.device_var.get().strip() or "auto",
                val_ratio=float(self.val_ratio_var.get()),
                seed=int(self.seed_var.get()),
                prepare_only=prepare_only,
            )
        except ValueError as exc:
            messagebox.showerror("Invalid training parameter", str(exc))
            return

        self._log("Starting training job...")
        self.training_thread = threading.Thread(target=self._training_worker, args=(request,), daemon=True)
        self.training_thread.start()

    def _training_worker(self, request: TrainingRequest) -> None:
        try:
            result = run_training(request, log=self.log_queue.put)
        except Exception as exc:
            self.log_queue.put(f"ERROR: {exc}")
            return

        self.log_queue.put(f"Done. Expected weights: {result.best_weights}")
        if result.best_weights.exists():
            self.selected_model_path = result.best_weights
            self.log_queue.put("New model selected. Use 'Promote as active' to load it in Autodrive.")
        self.log_queue.put("__REFRESH_MODELS__")

    def _drain_logs(self) -> None:
        while True:
            try:
                message = self.log_queue.get_nowait()
            except queue.Empty:
                break
            if message == "__REFRESH_MODELS__":
                self.refresh_models()
                continue
            self._log(message)
        self.after(120, self._drain_logs)

    def _log(self, message: str) -> None:
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")

    def on_close(self) -> None:
        self.close_capture_camera()
        self.destroy()


def main() -> None:
    app = ModelTrainerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
