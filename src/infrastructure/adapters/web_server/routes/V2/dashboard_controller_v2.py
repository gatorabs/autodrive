from flask import jsonify, request
from src.domain.services.os.python_process_service import get_active_python_processes


def process_api_info(app, shared_controls):
    @app.route('/api/v2/python-processes', methods=['GET'])
    def python_processes():
        return jsonify(get_active_python_processes())

    @app.route('/api/v2/manual-mode', methods=['POST'])
    def manual_mode():
        data = request.get_json(silent=True) or {}
        active = data.get('active', True)
        shared_controls["MANUAL_MD"] = bool(active)
        return jsonify({"manual_mode": shared_controls["MANUAL_MD"]})

    @app.route('/api/v2/manual-controls', methods=['POST'])
    def manual_controls():
        data = request.get_json(silent=True) or {}
        x = float(data.get('x', 0.0))
        y = float(data.get('y', 0.0))

        direction = int(90 + max(min(x, 1.0), -1.0) * 90)
        direction = max(0, min(180, direction))

        speed = int(max(min(y, 1.0), 0.0) * 255)
        speed = max(0, min(255, speed))

        car_info = shared_controls.get("CAR_INFO", {})
        car_info["CAR_DIRECTION_DATA"] = direction
        car_info["CAR_SPEED_DATA"] = speed
        shared_controls["CAR_INFO"] = car_info

        return jsonify({"direction": direction, "speed": speed})
