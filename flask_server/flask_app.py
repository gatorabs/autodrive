from flask import Flask, Response, render_template, jsonify
import time
import numpy as np
import cv2
from flask_cors import CORS

from processing.priorities_processor import set_process_priority

app = Flask(__name__)
CORS(app)
shared_frames = None
shared_controls = None

@app.route('/api/direction')
def get_direction():
    direction = 0
    running = False
    if shared_controls is not None:
        direction = shared_controls.get("direction", 0)
        running = shared_controls.get("RUNNING", False)

    return jsonify({"direction": direction, "running": running})


def generate_placeholder_image():
    img = np.zeros((270, 480, 3), dtype=np.uint8)
    cv2.putText(img, "Carregando Detector...", (50, 135),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    ret, jpeg = cv2.imencode('.jpg', img)
    return jpeg.tobytes()

def generate_feed(key):
    last_time = 0
    interval = 0.05

    while True:
        now = time.time()
        if now - last_time < interval:
            continue

        last_time = now
        if shared_frames and key in shared_frames:
            frame = shared_frames[key]
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                if key == "object":
                    placeholder = generate_placeholder_image()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + placeholder + b'\r\n')
        else:
            if key == "object":
                placeholder = generate_placeholder_image()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + placeholder + b'\r\n')


@app.route('/video_feed/<string:key>')
def video_feed(key):
    response = Response(generate_feed(key), mimetype='multipart/x-mixed-replace; boundary=frame')
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


def start_flask_server(frames_dict, controls_dict):
    global shared_frames, shared_controls
    shared_frames = frames_dict
    shared_controls = controls_dict
    app.run(host='0.0.0.0', port=5000)
