import argparse
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np
import yaml


def parse_args():
    parser = argparse.ArgumentParser(
        description="Captura imagens com bounding boxes para treinar modelos YOLO."
    )
    parser.add_argument(
        "--base-dir",
        default="dataset",
        help=(
            "Diretório base onde as capturas serão armazenadas. Para múltiplos objetos, "
            "cada um ganhará uma subpasta própria."
        ),
    )
    parser.add_argument(
        "--objects",
        type=int,
        help="Número de objetos/classe que serão capturados nesta sessão."
    )
    parser.add_argument(
        "--class-names",
        nargs="+",
        help="Nomes (opcionais) para cada objeto. Define também a quantidade de objetos."
    )
    parser.add_argument(
        "--target-fps",
        type=float,
        default=2.0,
        help="Taxa máxima de salvamento automático em quadros por segundo.",
    )
    parser.add_argument(
        "--save-when-no-box",
        action="store_true",
        help="Permite salvar imagens mesmo quando o tracker perdeu o alvo.",
    )
    return parser.parse_args()


def slugify(value: str, fallback: str) -> str:
    value = re.sub(r"[^0-9a-zA-Z_-]+", "-", value.strip())
    value = re.sub(r"-+", "-", value).strip("-_")
    return value or fallback


def _relpath_for_config(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except ValueError:
        pass

    try:
        return os.path.relpath(path, base)
    except (ValueError, OSError):
        return str(path.resolve())


def ask_int(prompt: str) -> int:
    while True:
        try:
            value = int(input(prompt))
        except ValueError:
            print("Digite um número inteiro válido.")
            continue
        if value < 1:
            print("Informe um valor maior ou igual a 1.")
            continue
        return value


def maybe_ask_names(count: int, provided: Optional[List[str]]) -> List[str]:
    names: List[str] = []
    if provided:
        if len(provided) != count:
            raise SystemExit(
                "Quantidade de nomes informados em --class-names difere do número de objetos."
            )
        return provided

    for idx in range(count):
        name = input(f"Nome do objeto {idx + 1} (opcional, Enter para usar padrão): ").strip()
        names.append(name or f"objeto_{idx + 1:02d}")
    return names


@dataclass
class ObjectSession:
    index: int
    name: str
    class_id: int
    root: Path
    images_dir: Path
    labels_dir: Path
    display_name: str
    saved: int = 0


args = parse_args()

if args.objects is not None:
    num_objects = max(1, args.objects)
elif args.class_names:
    num_objects = len(args.class_names)
else:
    num_objects = ask_int("Quantos objetos deseja capturar nesta sessão? ")

raw_names = maybe_ask_names(num_objects, args.class_names)

base_dir = Path(args.base_dir)
sessions: List[ObjectSession] = []

for idx, raw_name in enumerate(raw_names):
    fallback = f"objeto_{idx + 1:02d}"
    slug = slugify(raw_name, fallback)
    display_name = raw_name or fallback
    if num_objects == 1:
        session_root = base_dir
    else:
        session_root = base_dir / slug
    images_dir = session_root / "images"
    labels_dir = session_root / "labels"
    images_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)
    sessions.append(
        ObjectSession(
            index=idx,
            name=raw_name,
            class_id=idx,
            root=session_root,
            images_dir=images_dir,
            labels_dir=labels_dir,
            display_name=display_name,
        )
    )

current_session = sessions[0]
TARGET_FPS = max(1e-3, args.target_fps)
SAVE_WHEN_NO_BOX = args.save_when_no_box

# --- utils ---
def bbox_to_yolo(x,y,w,h,img_w,img_h):
    xc=(x+w/2)/img_w; yc=(y+h/2)/img_h; wn=w/img_w; hn=h/img_h
    return xc,yc,wn,hn

def laplacian_var(gray):
    return cv2.Laplacian(gray, cv2.CV_64F).var()

def inside(img_w,img_h,x,y,w,h,margin=2):
    return x>=margin and y>=margin and x+w<=img_w-margin and y+h<=img_h-margin and w>4 and h>4

# desenhar caixa para inicializar
drawing=False; box_start=None; init_box=None  # init_box: (x,y,w,h) em ints
def on_mouse(event,x,y,flags,param):
    global drawing, box_start, init_box
    if event==cv2.EVENT_LBUTTONDOWN:
        drawing=True
        box_start=(x,y)
        init_box=None  # começando nova bbox
    elif event==cv2.EVENT_MOUSEMOVE and drawing:
        x1,y1=box_start; x2,y2=x,y
        x1,x2=min(x1,x2),max(x1,x2)
        y1,y2=min(y1,y2),max(y1,y2)
        init_box=(x1,y1,x2-x1,y2-y1)
    elif event==cv2.EVENT_LBUTTONUP:
        drawing=False
        # garante bbox mesmo se quase não houve movimento
        x1,y1=box_start; x2,y2=x,y
        x1,x2=min(x1,x2),max(x1,x2)
        y1,y2=min(y1,y2),max(y1,y2)
        w=max(1, x2-x1); h=max(1, y2-y1)
        init_box=(x1,y1,w,h)

cap=cv2.VideoCapture(0)
if not cap.isOpened():
    raise SystemExit("Webcam indisponível.")

win="webcam"
cv2.namedWindow(win)
cv2.setMouseCallback(win,on_mouse)


def create_tracker():
    if hasattr(cv2, "legacy"):
        return cv2.legacy.TrackerCSRT_create()
    return cv2.TrackerCSRT_create()


def describe_current_session() -> List[str]:
    display_name = current_session.name or f"classe_{current_session.class_id}"
    folder_info = current_session.root if num_objects > 1 else base_dir
    folder_str = str(folder_info)
    return [
        "'Clique e arraste' para definir bbox inicial",
        "'t' iniciar/parar tracking  |  'r' redefinir bbox  |  's' gravar on/off",
        "'Space' salvar manual  |  'h' próximo objeto  |  'q' sair",
        f"Objeto atual ({current_session.index + 1}/{num_objects}): classe={current_session.class_id}  nome='{display_name}'",
        f"Saída: {folder_str}",
    ]


def reset_state():
    global tracker, tracking, saving, init_box, box_start, prev_center, last_save
    tracker=None
    tracking=False
    saving=False
    init_box=None
    box_start=None
    prev_center=None
    last_save=0.0


tracker=None
tracking=False
saving=False
prev_center=None
last_save=0.0
save_interval=1.0 / TARGET_FPS

help_lines = describe_current_session()

while True:
    ok_frame,frame=cap.read()
    if not ok_frame:
        break
    h,w=frame.shape[:2]
    disp=frame.copy()

    if init_box is not None and drawing:
        x,y,bb_w,bb_h=init_box
        cv2.rectangle(disp,(x,y),(x+bb_w,y+bb_h),(0,255,0),2)
    elif init_box is not None and not drawing and not tracking:
        x,y,bb_w,bb_h=init_box
        cv2.rectangle(disp,(x,y),(x+bb_w,y+bb_h),(0,255,0),2)
        cv2.putText(disp,"BBox pronta: pressione 't' para iniciar tracking",
                    (10,30), cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,255,0),2)

    if tracking and tracker is not None:
        ok_track,bbox=tracker.update(frame)
        if ok_track:
            x,y,bb_w,bb_h = [int(v) for v in bbox]
            stable = inside(w,h,x,y,bb_w,bb_h)
            gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
            sharp = laplacian_var(gray)
            center=(x+bb_w/2, y+bb_h/2)
            jump = 0 if prev_center is None else np.hypot(center[0]-prev_center[0], center[1]-prev_center[1])
            prev_center=center

            sharp_ok = sharp > 60
            jump_ok  = jump < max(bb_w,bb_h) * 0.35

            cv2.rectangle(disp,(x,y),(x+bb_w,y+bb_h),(0,255,0),2)
            cv2.putText(disp,f"sharp={sharp:.0f} jump={jump:.1f}",(10,20),
                        cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,255,255),2)

            now=time.time()
            if saving and (now-last_save)>=save_interval:
                if (stable and sharp_ok and jump_ok) or SAVE_WHEN_NO_BOX:
                    ts=datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    img=f"{ts}.jpg"
                    pimg=current_session.images_dir / img
                    cv2.imwrite(str(pimg), frame)
                    lab=img.replace(".jpg",".txt")
                    plab=current_session.labels_dir / lab
                    if stable:
                        xc,yc,wn,hn=bbox_to_yolo(x,y,bb_w,bb_h,w,h)
                        with open(plab,"w") as f:
                            f.write(f"{current_session.class_id} {xc:.6f} {yc:.6f} {wn:.6f} {hn:.6f}\n")
                    else:
                        open(plab,"w").close()
                    current_session.saved += 1
                    last_save=now
        else:
            cv2.putText(disp,"[tracker perdeu o alvo] Pressione 'r' para redefinir bbox",
                        (10, h-20), cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,0,255),2)
            saving=False

    for i,t in enumerate(help_lines):
        cv2.putText(disp,t,(10,60+20*i),cv2.FONT_HERSHEY_SIMPLEX,0.5,(220,220,220),1)

    cv2.putText(
        disp,
        (
            f"Tracking: {'ON' if tracking else 'OFF'}   "
            f"Recording: {'ON' if saving else 'OFF'}   "
            f"capturadas={current_session.saved}"
        ),
        (10,h-50),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255,255,255),
        2,
    )

    cv2.imshow(win,disp)
    key=cv2.waitKey(1)&0xFF

    if key==ord('t'):
        if tracking:
            tracking=False
            tracker=None
            prev_center=None
        else:
            if init_box is not None and not drawing:
                x,y,bb_w,bb_h = [int(v) for v in init_box]
                if bb_w > 1 and bb_h > 1:
                    tracker=create_tracker()
                    tracker.init(frame, (x,y,bb_w,bb_h))
                    tracking=True
                    prev_center=None
            else:
                print("Defina a bbox (clique/arraste) e solte o mouse antes de 't'.")
    elif key==ord('r'):
        tracking=False
        tracker=None
        prev_center=None
        init_box=None
    elif key==ord('s'):
        saving=not saving
        last_save=0.0
    elif key==32: # Space
        use=None
        if tracking and tracker is not None:
            ok_track,bbox=tracker.update(frame)
            if ok_track:
                use=[int(v) for v in bbox]
        elif init_box is not None and not drawing:
            use=[int(v) for v in init_box]

        ts=datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        img=f"{ts}.jpg"
        pimg=current_session.images_dir / img
        cv2.imwrite(str(pimg), frame)
        lab=img.replace(".jpg",".txt")
        plab=current_session.labels_dir / lab
        if use is not None and use[2] > 1 and use[3] > 1:
            x,y,bb_w,bb_h=use
            xc,yc,wn,hn=bbox_to_yolo(x,y,bb_w,bb_h,w,h)
            with open(plab,"w") as f:
                f.write(f"{current_session.class_id} {xc:.6f} {yc:.6f} {wn:.6f} {hn:.6f}\n")
        else:
            open(plab,"w").close()
        current_session.saved += 1
    elif key==ord('h'):
        if current_session.index + 1 < num_objects:
            current_session = sessions[current_session.index + 1]
            help_lines = describe_current_session()
            reset_state()
            print(
                f"Alterando para objeto {current_session.index + 1}/{num_objects}: "
                f"classe={current_session.class_id} nome='{current_session.name}'"
            )
        else:
            print("Você já está no último objeto configurado.")
    elif key==ord('q') or key==27:
        break

cap.release()
cv2.destroyAllWindows()


def generate_data_yaml(session: ObjectSession) -> Path:
    """Cria um ``data.yaml`` simples apontando para o dataset capturado."""

    yaml_path = session.root / "data.yaml"
    data = {
        "path": str(session.root.resolve()),
        "train": "images",
        "val": "images",
        "names": {session.class_id: session.display_name},
    }

    with yaml_path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, allow_unicode=True, sort_keys=False)

    return yaml_path


if sessions:
    print("\nGerando arquivos data.yaml para os datasets capturados...")
    for sess in sessions:
        yaml_path = generate_data_yaml(sess)
        print(f" - {yaml_path}")
    print(
        "Cada arquivo aponta para as pastas images/ e labels capturadas. "
        "Ajuste conforme necessário antes do treinamento."
    )


def generate_training_config(sessions: List[ObjectSession], base_dir: Path) -> Path:
    """Cria (ou atualiza) um arquivo ``training_config.auto.yaml`` com os modelos."""

    config_dir = Path(__file__).resolve().parent
    config_path = config_dir / "training_config.auto.yaml"

    models = []
    for sess in sessions:
        dataset_ref = _relpath_for_config(sess.root.resolve(), config_dir)
        model_name = slugify(sess.display_name, f"modelo_{sess.index + 1:02d}")

        models.append(
            {
                "name": model_name,
                "dataset": dataset_ref,
                "classes": [sess.display_name],
                "output": f"yolo_runs/{model_name}",
                "val_ratio": 0.2,
                "train": {},
            }
        )

    config_payload = {
        "auto_generated": True,
        "base_dataset": _relpath_for_config(base_dir.resolve(), config_dir),
        "models": models,
    }

    with config_path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(config_payload, fh, allow_unicode=True, sort_keys=False)

    return config_path


if sessions:
    config_file = generate_training_config(sessions, base_dir)
    print(
        "\nArquivo de configuração agregado gerado em "
        f"{config_file}. Use-o diretamente com train_models.py."
    )
