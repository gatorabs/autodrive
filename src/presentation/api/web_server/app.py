from flask import Flask
from flask_cors import CORS
from src.presentation.api.web_server.routes.V1.dashboard_controller_v1 import car_api_info, video_api_info
from src.presentation.api.web_server.routes.V2.dashboard_controller_v2 import process_api_info
from src.presentation.api.web_server.routes.V1.app_controller import shutdown_server
from src.infrastructure.logging.logger import Logger
from src.infrastructure.logging.werkzeug_filters import SuppressCodesFilter
import logging
shared_frames = {}
shared_controls = {}
from flask import render_template

logger = Logger("FlaskServer")

logging.getLogger('werkzeug').addFilter(SuppressCodesFilter())

def create_app(frames_dict, controls_dict):
    global shared_frames, shared_controls
    shared_frames = frames_dict
    shared_controls = controls_dict

    app = Flask(__name__, template_folder="templates", static_folder="static")

    CORS(app)
    shutdown_server(app)
    car_api_info(app, shared_controls)
    video_api_info(app, shared_frames, logger)
    process_api_info(app, shared_controls)

    @app.route('/speed')
    def speed_page():
        return render_template('speed_control.html')

    return app

def start_flask_server(frames_dict, controls_dict):
    app = create_app(frames_dict, controls_dict)
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=False, use_reloader=False)
