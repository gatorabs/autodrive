# prepare_yolo_dataset.py
import os, random, shutil, yaml, glob

DATASET_DIR = "dataset"
IMG_DIR = os.path.join(DATASET_DIR, "images")
LAB_DIR = os.path.join(DATASET_DIR, "labels")
OUT = "yolo_data"  # pasta nova com train/val organizados
VAL_RATIO = 0.2    # 20% para validação
CLASS_NAMES = ["objeto"]  # ajuste seus nomes aqui (ordem = IDs)

random.seed(42)
os.makedirs(OUT, exist_ok=True)
for split in ["train", "val"]:
    os.makedirs(os.path.join(OUT, "images", split), exist_ok=True)
    os.makedirs(os.path.join(OUT, "labels", split), exist_ok=True)

imgs = sorted(glob.glob(os.path.join(IMG_DIR, "*.jpg")) + glob.glob(os.path.join(IMG_DIR, "*.png")))
pairs = []
for img in imgs:
    base = os.path.splitext(os.path.basename(img))[0]
    lab = os.path.join(LAB_DIR, base + ".txt")
    if os.path.exists(lab):
        pairs.append((img, lab))

random.shuffle(pairs)
n_val = int(len(pairs) * VAL_RATIO)
val_pairs = pairs[:n_val]
train_pairs = pairs[n_val:]

def copy_pairs(pairs, split):
    for img, lab in pairs:
        shutil.copy2(img, os.path.join(OUT, "images", split, os.path.basename(img)))
        shutil.copy2(lab, os.path.join(OUT, "labels", split, os.path.basename(lab)))

copy_pairs(train_pairs, "train")
copy_pairs(val_pairs, "val")

# cria data.yaml
data = {
    "path": os.path.abspath(OUT),
    "train": "images/train",
    "val": "images/val",
    "names": {i: n for i, n in enumerate(CLASS_NAMES)},
}
with open(os.path.join(OUT, "data.yaml"), "w") as f:
    yaml.safe_dump(data, f, sort_keys=False)

print("Feito!")
print("Total pares:", len(pairs), "| train:", len(train_pairs), "| val:", len(val_pairs))
print("Edite 'CLASS_NAMES' no script se tiver mais classes.")
