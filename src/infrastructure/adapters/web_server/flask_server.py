from flask import Flask, Response, render_template, jsonify, stream_with_context
import time
import numpy as np
import cv2
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

shared_frames = None
shared_controls = None

def start_flask_server(frames_dict, controls_dict):
    global shared_frames, shared_controls
    shared_frames = frames_dict
    shared_controls = controls_dict
    app.run(host='0.0.0.0', port=5000)

@app.route('/api/car_info')
def get_car_info():
    info = {
        "running":  False,
        "car_info": {},
        "arrow":    None,
        "time_info": []
    }
    if shared_controls:
        info["running"]   = shared_controls.get("RUNNING", False)
        info["car_info"]  = shared_controls.get("car_info", {})
        info["arrow"]     = shared_controls.get("ARROW", None)
        info["time_info"] = shared_controls.get("time_info", [])
    return jsonify(info)

@app.route('/video_feed/<string:key>')
def video_feed(key):
    return Response(
        stream_with_context(generate_feed(key)),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

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

