import cv2
import os, time
from datetime import datetime
import numpy as np

OUTPUT_DIR="dataset"; IMG_DIR="images"; LAB_DIR="labels"
os.makedirs(os.path.join(OUTPUT_DIR, IMG_DIR), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, LAB_DIR), exist_ok=True)

CLASS_ID=0
TARGET_FPS=2.0
SAVE_WHEN_NO_BOX=False

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
if not cap.isOpened(): raise SystemExit("Webcam indisponível.")

win="webcam"; cv2.namedWindow(win); cv2.setMouseCallback(win,on_mouse)

# tracker: escolha CSRT (mais estável) ou KCF (mais rápido)
def create_tracker():
    if hasattr(cv2, "legacy"):
        return cv2.legacy.TrackerCSRT_create()
    return cv2.TrackerCSRT_create()

tracker=None; tracking=False
saving=False; last_save=0; save_interval=1.0/max(1e-6, TARGET_FPS)
img_count=0
prev_center=None

help_lines=[
    "'Clique e arraste' para definir bbox inicial",
    "'t' iniciar/parar tracking  |  'r' redefinir bbox  |  's' gravar on/off",
    "'Space' salvar manual  |  'q' sair"
]

while True:
    ok_frame,frame=cap.read()
    if not ok_frame: break
    h,w=frame.shape[:2]
    disp=frame.copy()

    # desenhar bbox: enquanto arrasta...
    if init_box is not None and drawing:
        x,y,bb_w,bb_h=init_box
        cv2.rectangle(disp,(x,y),(x+bb_w,y+bb_h),(0,255,0),2)
    # ...e manter após soltar (aqui estava faltando no seu código)
    elif init_box is not None and not drawing and not tracking:
        x,y,bb_w,bb_h=init_box
        cv2.rectangle(disp,(x,y),(x+bb_w,y+bb_h),(0,255,0),2)
        cv2.putText(disp,"BBox pronta: pressione 't' para iniciar tracking",
                    (10,30), cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,255,0),2)

    # atualizar tracker
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
                    img=f"{ts}.jpg"; pimg=os.path.join(OUTPUT_DIR,IMG_DIR,img)
                    cv2.imwrite(pimg, frame)
                    lab=img.replace(".jpg",".txt"); plab=os.path.join(OUTPUT_DIR,LAB_DIR,lab)
                    if stable:
                        xc,yc,wn,hn=bbox_to_yolo(x,y,bb_w,bb_h,w,h)
                        with open(plab,"w") as f:
                            f.write(f"{CLASS_ID} {xc:.6f} {yc:.6f} {wn:.6f} {hn:.6f}\n")
                    else:
                        open(plab,"w").close()
                    img_count+=1; last_save=now
        else:
            cv2.putText(disp,"[tracker perdeu o alvo] Pressione 'r' para redefinir bbox",
                        (10, h-20), cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,0,255),2)
            # opcional: pausar gravação quando perder
            saving=False

    # overlays
    y0=60
    for i,t in enumerate(help_lines):
        cv2.putText(disp,t,(10,y0+20*i),cv2.FONT_HERSHEY_SIMPLEX,0.5,(220,220,220),1)
    cv2.putText(disp,f"Tracking: {'ON' if tracking else 'OFF'}   Recording: {'ON' if saving else 'OFF'}   saved={img_count}",
                (10,h-50),cv2.FONT_HERSHEY_SIMPLEX,0.6,(255,255,255),2)

    cv2.imshow(win,disp)
    key=cv2.waitKey(1)&0xFF

    if key==ord('t'):
        # iniciar/parar tracking (precisa de init_box finalizada)
        if tracking:
            tracking=False; tracker=None; prev_center=None
        else:
            if init_box is not None and not drawing:
                # garante inteiros e área > 0
                x,y,bb_w,bb_h = [int(v) for v in init_box]
                if bb_w > 1 and bb_h > 1:
                    tracker=create_tracker()
                    tracker.init(frame, (x,y,bb_w,bb_h))
                    tracking=True; prev_center=None
            else:
                print("Defina a bbox (clique/arraste) e solte o mouse antes de 't'.")
    elif key==ord('r'):
        tracking=False; tracker=None; prev_center=None; init_box=None
    elif key==ord('s'):
        saving=not saving; last_save=0
    elif key==32: # Space: salvar manual
        # usa bbox do tracker (se ativo) ou a init_box parada
        use=None
        if tracking and tracker is not None:
            ok_track,bbox=tracker.update(frame)
            if ok_track: use=[int(v) for v in bbox]
        elif init_box is not None and not drawing:
            use=[int(v) for v in init_box]

        ts=datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        img=f"{ts}.jpg"; pimg=os.path.join(OUTPUT_DIR,IMG_DIR,img)
        cv2.imwrite(pimg, frame)
        lab=img.replace(".jpg",".txt"); plab=os.path.join(OUTPUT_DIR,LAB_DIR,lab)
        if use is not None and use[2] > 1 and use[3] > 1:
            x,y,bb_w,bb_h=use
            xc,yc,wn,hn=bbox_to_yolo(x,y,bb_w,bb_h,w,h)
            with open(plab,"w") as f:
                f.write(f"{CLASS_ID} {xc:.6f} {yc:.6f} {wn:.6f} {hn:.6f}\n")
        else:
            open(plab,"w").close()
    elif key==ord('q') or key==27:
        break

cap.release(); cv2.destroyAllWindows()
