from flask import jsonify, request
from src.infrastructure.hardware.process_monitor import get_active_python_processes
from src.infrastructure.mappers.direction_mapper import map_range


def process_api_info(app, shared_controls):
    @app.route('/api/v2/python-processes', methods=['GET'])
    def python_processes():
        return jsonify(get_active_python_processes())

    @app.route('/api/v2/manual-mode', methods=['POST'])
    def manual_mode():
        data = request.get_json(silent=True) or {}
        active = data.get('active', True)
        shared_controls.manual_mode = bool(active)
        return jsonify({"manual_mode": shared_controls.manual_mode})

    @app.route('/api/v2/manual-controls', methods=['POST'])
    def manual_controls():
        data = request.get_json(silent=True) or {}
        x = float(data.get('x', 0.0))
        y = float(data.get('y', 0.0))

        direction = map_range(x, -1.0, 1.0, 0, 180, clamp_value=True)
        speed = map_range(y, 0.0, 1.0, 0, 255, clamp_value=True)

        car_info = shared_controls.car_info or {}
        car_info["CAR_DIRECTION_DATA"] = direction
        car_info["CAR_SPEED_DATA"] = speed
        shared_controls.car_info = car_info

        return {"direction": direction, "speed": speed}, 200
