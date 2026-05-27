# Autodrive Model Trainer

Run this file from PyCharm:

```text
utils/model_trainer/run_trainer.py
```

The trainer UI is the recommended flow. It opens a camera for live image
capture, lets you draw a bounding box, tracks the object, saves YOLO
image/label pairs, validates datasets, prepares the composed `todos_objetos`
model, streams training logs, lists trained weights, and promotes one weight as
the active model used by Autodrive.

## Folder Layout

- `run_trainer.py`: main entrypoint to execute.
- `app/`: CustomTkinter UI.
- `services/`: camera capture, dataset inspection, dataset preparation,
  training, and model registry logic.
- `cli/`: auxiliary command-line scripts for capture, legacy training, and
  webcam inference tests.
- `dataset/`: local datasets, ignored by Git.
- `yolo_runs/` and `runs/`: local training outputs, ignored by Git.

Promoting a model only updates `config/model_registry.json`; it does not copy,
delete, or overwrite existing weights.
