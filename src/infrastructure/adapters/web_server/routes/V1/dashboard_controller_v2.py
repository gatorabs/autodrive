from flask import jsonify
from src.application.services.process_service import ProcessManager

def process_api_info(app):
    @app.route('/api/v2/python-processes', methods=['GET'])
    def python_processes():
        return jsonify(ProcessManager.get_active_python_processes())
