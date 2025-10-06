import cv2
from ultralytics import YOLO
import torch

MODEL_PATH = "runs/detect/train/weights/best.pt"  # ajuste o caminho
device = 0 if torch.cuda.is_available() else "cpu"  # usa GPU se tiver

model = YOLO(MODEL_PATH)
cap = cv2.VideoCapture(0)

# opcional: definir resolução/fps da webcam
cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cap.set(cv2.CAP_PROP_FPS, 30)

while True:
    ok, frame = cap.read()
    if not ok:
        break

    # inferência (ajuste conf/imgsz conforme sua máquina)
    results = model.predict(
        frame, conf=0.3, imgsz=640, device=device, verbose=False
    )

    # desenha caixas/labels
    annotated = results[0].plot()
    cv2.imshow("YOLO - Webcam", annotated)

    if cv2.waitKey(1) & 0xFF in (27, ord('q')):
        break

cap.release()
cv2.destroyAllWindows()
