# -*- coding: utf-8 -*-

import os

import wootpaste.blueprint as blueprint
from wootpaste.config import config
from wootpaste import mail
from wootpaste.utils.filters import ViewFilters

from flask import Flask, g
from flask_wtf.csrf import CsrfProtect
from flask.ext.assets import Environment, Bundle
from webassets.filter import get_filter


def create_app():
    app = Flask(__name__,                       
        static_url_path='',
        static_folder='../public',
        template_folder='../views')
    app.config.update(config['flask'])
    CsrfProtect(app)

    mail.init_app(app)

    ViewFilters.register(app)

    assets = Environment(app)
    assets.url = app.static_url_path

    css_bundle = Bundle('style.sass', filters='sass,cssmin', output='bundle.min.css')
    assets.register('css_all', css_bundle)
    js_bundle = Bundle('js/*.js', output='bundle.min.js') # filters='jsmin', 
    assets.register('js_all', js_bundle)

    blueprint.register(app)

    return app

