# -*- coding: utf-8 -*-

from frontend import blueprint as frontend

def register(app):
    app.register_blueprint(frontend)

