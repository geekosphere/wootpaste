from werkzeug.serving import run_simple
from werkzeug.wsgi import DispatcherMiddleware

from wootpaste import app as wootapp

application = DispatcherMiddleware(wootapp.create_app())

if __name__ == "__main__":
    run_simple('0.0.0.0', 4000, application, use_reloader=True, use_debugger=True)

