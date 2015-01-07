# -*- coding: utf-8 -*-

import os
from functools import partial

import wootpaste.blueprint as blueprint
from wootpaste.config import config
from wootpaste import mail
from wootpaste.models import Paste
from wootpaste.database import db_session
from wootpaste.utils import approot
from wootpaste.utils.filters import ViewFilters

if config['paste.spam_ml']:
    import wootpaste.utils.spam_ml as spam_ml

from flask import Flask, g, redirect, Blueprint
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
    assets.load_path = [
        app.static_folder,
        approot('bower_components')
    ]
    assets.url = app.static_url_path

    if app.debug:
        css_filters = 'sass,cssmin'
        js_filters = 'jsmin'
    else:
        css_filters = 'sass'
        js_filters = None

    css_bundle = Bundle('style.sass', filters=css_filters, output='bundle.min.css')
    assets.register('css_all', css_bundle)
    js_bundle = Bundle('jquery/dist/jquery.js', 'sjcl/sjcl.js', 'jquery-qrcode/jquery.qrcode.min.js', 'js/*.js', filters=js_filters, output='bundle.min.js')
    assets.register('js_all', js_bundle)

    app.register_blueprint(Blueprint(
        'bower', __name__, static_url_path='/bower', static_folder=approot('bower_components')))

    blueprint.register(app)

    for paste in db_session.query(Paste.key).filter_by(legacy=True).all():
        route = u'/' + paste.key
        app.add_url_rule(route, 'legacy_show_'+paste.key, partial(redirect, '/paste/' + paste.key))

    if config['paste.spam_ml']:
        spam_ml.load()

    return app

