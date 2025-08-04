from flask import jsonify
from src.application.services.python_process_service import get_active_python_processes

def process_api_info(app):
    @app.route('/api/v2/python-processes', methods=['GET'])
    def python_processes():
        return jsonify(get_active_python_processes())
