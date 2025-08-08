from src.infrastructure.adapters.video.video_utility_process import generate_placeholder_image, encode_frame
from src.infrastructure.adapters.web_server import app_settings
from flask import Response, jsonify
import time

def car_api_info(app, shared_controls):
    @app.route('/api/car-info')
    def get_car_info():
        if getattr(app_settings, "shutdown_pending", False):
            return jsonify({"error": "Server is shutting down"}), 503
        info = {
            "running": shared_controls.get("RUNNING", False),
            "car_info": shared_controls.get("CAR_INFO", {}),
            "time_info": shared_controls.get("TIME_INFO", [])
        }
        return jsonify(info)

def video_api_info(app, shared_frames, logger):
    @app.route('/video_feed/<string:key>')
    def video_feed(key):
        if getattr(app_settings, "shutdown_pending", False):
            return 'Server is shutting down', 503
        return Response(
            generate_feed(shared_frames, key, logger),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )

    def generate_feed(shared_frames, key, logger):
        interval = 0.05
        last_time = time.time()

        def yield_placeholder():
            try:
                placeholder = generate_placeholder_image()
                return (b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + placeholder + b'\r\n')
            except Exception as e:
                logger.error(f"Erro ao gerar placeholder: {e}")
                return b''

        while True:
            if getattr(app_settings, "shutdown_pending", False):
                break

            now = time.time()
            if now - last_time < interval:
                continue

            last_time = now

            try:
                frame = shared_frames.get(key)
                if frame is not None:
                    encoded = encode_frame(frame)
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + encoded + b'\r\n')
                else:
                    yield yield_placeholder()
            except Exception as e:
                logger.error(f"Erro no streaming '{key}': {e}")
                break
