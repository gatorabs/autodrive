from flask import Flask
from flask_cors import CORS
from src.infrastructure.adapters.web_server.routes.V1.dashboard_controller_v1 import car_api_info, video_api_info
from src.infrastructure.logging.logger import Logger
shared_frames = {}
shared_controls = {}

logger = Logger("FlaskServer")

def create_app(frames_dict, controls_dict):
    global shared_frames, shared_controls
    shared_frames = frames_dict
    shared_controls = controls_dict

    app = Flask(__name__)
    CORS(app)

    car_api_info(app, shared_controls)
    video_api_info(app, shared_frames, logger)

    return app

def start_flask_server(frames_dict, controls_dict):
    app = create_app(frames_dict, controls_dict)
    app.run(host='0.0.0.0', port=5000, threaded=True)
