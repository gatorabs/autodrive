from flask import Response, stream_with_context, jsonify
from src.infrastructure.adapters.video.video_toggle_process import  generate_placeholder_image
import time

def car_api_info(app, shared_controls):
    @app.route('/api/car_info')
    def get_car_info():
        info = {
            "running":  False,
            "car_info": {},
            "time_info": []
        }
        if shared_controls:
            info["running"]   = shared_controls.get("RUNNING", False)
            info["car_info"]  = shared_controls.get("CAR_INFO", {})
            info["time_info"] = shared_controls.get("TIME_INFO", [])
        return jsonify(info)

def video_api_info(app, shared_frames, logger):

    @app.route('/video_feed/<string:key>')
    def video_feed(key):
        return Response(
            stream_with_context(generate_feed(shared_frames, key)),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )

    def generate_feed(shared_frames, key):
        last_time = 0
        interval = 0.05

        def yield_placeholder():
            placeholder = generate_placeholder_image()
            return (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + placeholder + b'\r\n')

        while True:
            now = time.time()
            if now - last_time < interval:
                continue

            last_time = now

            try:
                frame = shared_frames.get(key, None)
                if frame:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                elif key == "OBJECT_FRAME":
                    yield yield_placeholder()
            except Exception as e:
                logger.info(f"Streaming de '{key}': {e}")
                break