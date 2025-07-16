from flask import Flask, request

def shutdown_server(app):
    @app.route('/shutdown', methods=['POST'])
    def shutdown():
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            return 'Not running with the Werkzeug Server', 500
        func()
        return 'Server shutting down...', 200
    return app