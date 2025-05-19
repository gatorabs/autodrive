from flask import Flask, Response, render_template
import time
import numpy as np
import cv2
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
shared_frames = None

@app.route('/')
def index():
    return render_template("index.html")

def generate_placeholder_image():
    img = np.zeros((270, 480, 3), dtype=np.uint8)
    cv2.putText(img, "Carregando Detector...", (50, 135),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    ret, jpeg = cv2.imencode('.jpg', img)
    return jpeg.tobytes()

def generate_feed(key):
    while True:
        if shared_frames and key in shared_frames:
            frame = shared_frames[key]
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                # Só para o key 'object', envia placeholder
                if key == "object":
                    placeholder = generate_placeholder_image()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + placeholder + b'\r\n')
                else:
                    time.sleep(0.1)
        else:
            # Se nem existe a key ainda no dict e for 'object' manda placeholder
            if key == "object":
                placeholder = generate_placeholder_image()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + placeholder + b'\r\n')
            else:
                time.sleep(0.1)

@app.route('/video_feed/<string:key>')
def video_feed(key):
    return Response(generate_feed(key), mimetype='multipart/x-mixed-replace; boundary=frame')

def start_flask_server(frames_dict):
    global shared_frames
    shared_frames = frames_dict
    app.run(host='0.0.0.0', port=5000)
