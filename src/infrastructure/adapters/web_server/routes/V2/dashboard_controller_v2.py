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
