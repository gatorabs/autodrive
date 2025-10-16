from src.infrastructure.adapters.video.video_utility_process import generate_placeholder_image
from src.infrastructure.utils.frame_utils import encode_frame
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
            "manual_mode": shared_controls.get("MANUAL_MD", False),
            "webview": shared_controls.get("WEBVIEW", False),
            "car_info": shared_controls.get("CAR_INFO", {}),
            "time_info": shared_controls.get("TIME_INFO", [])
        }
        return jsonify(info)

    @app.route('/api/set-speed', methods=['POST'])
    def set_speed():
        try:
            data = request.get_json()
            speed = data.get("speed")

            if not isinstance(speed, (int, float)) or speed < 0:
                return jsonify({"error": "Invalid speed value"}), 400

            shared_controls["SPEED"] = speed
            return jsonify({"message": f"Speed set to {speed}"}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

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
        interval = 0.03
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

