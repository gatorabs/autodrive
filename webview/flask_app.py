# flask_app.py
from flask import Flask, Response, render_template
import time

app = Flask(__name__)
shared_frames = None

@app.route('/')
def index():
    return render_template("index.html")

def generate_feed(key):
    while True:
        if shared_frames and key in shared_frames:
            frame = shared_frames[key]
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            time.sleep(0.1)

@app.route('/video_feed/<string:key>')
def video_feed(key):
    return Response(generate_feed(key), mimetype='multipart/x-mixed-replace; boundary=frame')

def start_flask_server(frames_dict):
    global shared_frames
    shared_frames = frames_dict
    app.run(host='0.0.0.0', port=5000)
