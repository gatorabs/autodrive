from flask import request, after_this_request
import threading
from src.presentation.api.web_server import app_settings

def shutdown_server(app):
    @app.route('/shutdown', methods=['POST'])
    def shutdown():
        app_settings.shutdown_pending = True
        func = request.environ.get('werkzeug.server.shutdown')

        @after_this_request
        def shutdown_after_response(response):
            def delayed_shutdown(shutdown_func):
                if shutdown_func is not None:
                    shutdown_func()
            threading.Thread(target=delayed_shutdown, args=(func,)).start()
            return response

        return 'Server shutting down...', 200
