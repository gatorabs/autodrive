from src.infrastructure.media.frame_codec import encode_frame
from src.infrastructure.vision.opencv_windows import generate_placeholder_image
from src.presentation.api.web_server import app_settings
from flask import Response, jsonify, request
import time

def car_api_info(app, shared_controls):
    @app.route('/api/car-info')
    def get_car_info():
        if getattr(app_settings, "shutdown_pending", False):
            return jsonify({"error": "Server is shutting down"}), 503
        info = {
            "running": shared_controls.is_running(),
            "manual_mode": shared_controls.manual_mode,
            "webview": shared_controls.webview,
            "car_info": shared_controls.car_info,
            "time_info": shared_controls.get("TIME_INFO", [])
        }
        return jsonify(info)

    @app.route('/api/set-speed', methods=['POST'])
    def set_speed():
        try:
            data = request.get_json(silent=True) or {}
            raw_speed = data.get("speed")

            if not isinstance(raw_speed, (int, float)):
                return jsonify({"error": "Invalid speed value"}), 400

            speed = int(round(raw_speed))
            speed = max(0, min(speed, 255))

            shared_controls["SPEED_OVERRIDE"] = speed

            car_info = dict(shared_controls.car_info or {})
            car_info["CAR_SPEED_DATA"] = speed
            shared_controls.car_info = car_info

            return jsonify({"message": f"Speed set to {speed}"}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

def video_api_info(app, shared_frames, logger):
    @app.route('/video_feed/<string:key>')
    def video_feed(key):
        if getattr(app_settings, "shutdown_pending", False):
            return 'Server is shutting down', 503
        if key == 'TAB2_FRAME':
            return 'Camera feed disabled for manual mode', 404
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

