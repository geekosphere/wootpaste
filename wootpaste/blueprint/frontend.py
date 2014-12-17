# -*- coding: utf-8 -*-

from forms import *
from errors import *

from wootpaste import mail
from wootpaste.database import db_session
from wootpaste.models import *
from wootpaste.utils.helpers import *
from wootpaste.utils import *

from flask import Response, Blueprint, g, jsonify, abort, request,\
    redirect, render_template, url_for, session

from flask.ext.mail import Message

import passlib.hash
from sqlalchemy.sql import func

from functools import wraps
from math import ceil
import datetime
import pytz
import json
import logging
logger = logging.getLogger('wootpaste')

blueprint = Blueprint('frontend', __name__, template_folder='templates')

@blueprint.before_request
def before_request():
    session.permanent = True
    # load default settings,
    #   current settings merged with defaults or
    #       user settings merged with defaults
    session['settings'] = SessionHelper.get_settings()

    # logged in?
    g.user = None
    g.is_admin = False
    if 'username' in session:
        res = User.query.filter_by(username=session['username'])
        if res.count():
            g.user = res.one()
            g.is_admin = g.user.admin
        else:
            del session['username']

    g.config = config

@blueprint.teardown_request
def teardown_request(exception):
    pass

@blueprint.errorhandler(404)
@blueprint.errorhandler(PasteNotFound)
def page_not_found(error):
    return render_template('error404.html'), 404

@blueprint.errorhandler(WootpasteError)
def custom_error(error):
    logger.error('application error: {}'.format(error.message))
    return render_template('error500.html', error=error), 500

"""
for the REST API:
@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response
"""

@blueprint.route('/', methods=['GET', 'POST'])
def paste_create():
    form = PasteForm(request.form)
    if request.method == 'POST' and form.validate():
        if request.form.get('subject', '') != '':
            raise SpamDetected()
        # only test using akismet if key configured, not logged in and not private paste
        if config['akismet_key'] and not g.user and not form.private.data:
            if AkismetHelper.check_spam(form.content):
                raise SpamDetected()
        if config['paste.block_links'] and '<a href="' in form.content.data:
            raise SpamDetected()
        paste = Paste()
        form.populate_obj(paste)
        if paste.encrypted:
            paste.private = True
        # the key is a unique identifier used in urls different from the serial id
        # the length is dependent on private/public
        # and xkcd keys are totally different
        paste.key = PasteHelper.get_free_key(paste.private, form.xkcd_ids.data)
        # the secret if known can be used by anyone to update/delete
        paste.secret = PasteHelper.get_secret()
        # ownership session:
        # the session needs a sid for this to work, we just use uuids:
        paste.owner_session = SessionHelper.get_session_id(session)
        paste.owner_user = SessionHelper.get_user_model()
        db_session.add(paste)
        db_session.commit()

        logger.info('paste created with key = {}'.format(paste.key))

        if form.irc_announce.data and config['irc_announce.active']:
            PasteHelper.irc_announce(paste)
        url = url_for('frontend.paste_show', key=paste.key)
        if request.is_xhr:
            return jsonify(url=url, key=paste.key)
        else:
            return redirect(url)

    return render_template('paste/create.html', form=form)

@blueprint.route('/edit/<key>', methods=['GET', 'POST'])
def paste_update(key):
    # to auth this:
    #   - secret must match
    #   - session sid must match
    # or- user must match
    paste = Paste.query.filter_by(key=key).one()
    if not PasteHelper.has_permission(paste): return redirect(url_for('frontend.login')) 
    form = PasteForm(request.form, obj=paste)
    if request.method == 'POST' and form.validate():
        form.populate_obj(paste)
        paste.updated_at = utcnow()
        db_session.commit()

        logger.info('paste updated, key = {}'.format(paste.key))

        url = url_for('frontend.paste_show', key=paste.key)
        if request.is_xhr:
            return jsonify(url=url, key=paste.key)
        else:
            return redirect(url)

    return render_template('paste/update.html', form=form, paste=paste)

@blueprint.route('/delete/<key>', methods=['GET', 'POST'])
def paste_delete(key):
    paste = Paste.query.filter_by(key=key).one()
    if not PasteHelper.has_permission(paste): return redirect(url_for('frontend.login')) 
    if request.method == 'POST':
        db_session.delete(paste)
        db_session.commit()
        logger.info('paste deleted, key = {}'.format(key))
        return redirect(url_for('frontend.paste_index'))

    return render_template('paste/delete.html', paste=paste)


@blueprint.route('/paste/<key>', defaults={'mode': None})
@blueprint.route('/paste/<key>/<mode>')
def paste_show(key, mode):
    res = Paste.query.filter_by(key=key)
    if not res.count(): raise PasteNotFound()
    paste = res.one()
    if PasteHelper.add_paste_visit(paste):
        raise PasteExpired()
    if not mode:
        return render_template('paste/show.html', paste=paste)
    elif mode == 'raw':
        return paste.content, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    elif mode == 'download':
        return paste.content, 200, {'Content-Type': 'text/plain; charset=utf-8',
                'Content-Disposition': 'attachment; filename='+paste.key+'.txt'}
    else:
        raise 'wrong mode'

@blueprint.route('/list')
def paste_index():
    pastes = Paste.query.filter_by(private=False, encrypted=False).order_by(Paste.created_at.desc())

    return render_template('paste/index.html', pastes=Pagination(pastes))

@blueprint.route('/user/<username>/public', defaults={'private': False})
@blueprint.route('/user/<username>/private', defaults={'private': True})
@blueprint.route('/user/<username>/all', defaults={'private': None})
def user_paste_index(username=None, private=None):
    if not g.user or g.user.username != username and private != False:
        if not g.is_admin: return redirect(url_for('frontend.login'))

    pastes = Paste.query.filter_by(encrypted=False).order_by(Paste.created_at.desc()).\
            join(User).filter(User.username == username)

    if private != None:
        pastes = pastes.filter(Paste.private == private)

    return render_template('paste/index.html', pastes=Pagination(pastes))

@blueprint.route('/pygments/<style>.css')
def pygments_style(style):
    return Response(PasteHelper.get_style(style), mimetype='text/css')

@blueprint.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm(request.form)
    if request.method == 'POST' and form.validate():
        user = User()
        user.username = form.username.data
        user.email = form.email.data
        # store encrypted (bcrypt) password
        user.password = PasswordHelper.encrypt(form.password.data)
        # store json of current settings in session
        user.settings = SessionHelper.get_settings_string()
        db_session.add(user)
        db_session.commit()

        logger.info('user signup, username = {}'.format(user.username))

        return redirect(url_for('frontend.login'))
    return render_template('user/signup.html', form=form)

@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        user = User.query.filter_by(username=form.username.data).one()
        session['username'] = user.username
        logger.info('user logged in, username = {}'.format(user.username))
        return redirect(url_for('frontend.paste_create'))
    return render_template('user/login.html', form=form)

@blueprint.route('/logout', methods=['GET', 'POST'])
def logout():
    if 'username' in session:
        logger.info('user logged out, username = {}'.format(session['username']))
        session.clear()
        return redirect(url_for('frontend.paste_create'))

@blueprint.route('/reset', methods=['GET', 'POST'])
def password_reset():
    form = PasswordResetForm(request.form)
    if request.method == 'POST' and form.validate():
        user = User.query.filter(User.username == form.username.data).one()

        token = get_token(32)
        base_url = request.host_url.rstrip('/')
        url = url_merge_param(base_url + url_for('frontend.password_reset2'),
                {'token': str(token)}) 

        db_session.add(UserReset(token=token, user_id=user.id))
        db_session.commit()

        msg = Message(config['password_reset.subject'],
            sender=config['password_reset.sender'], recipients=[user.email])
        msg.body = config['password_reset.content'].format(token=token, url=url)
        mail.send(msg)

        logger.info('user password reset, sent token to {} for user {}'.format(user.email, user.username))

        return redirect(url_for('frontend.password_reset2'))
    return render_template('user/reset.html', form=form)

@blueprint.route('/reset2', methods=['GET', 'POST'])
def password_reset2():
    if request.method == 'GET':
        form = PasswordResetTokenForm(data={'token': request.args.get('token')})
    else:
        form = PasswordResetTokenForm(request.form)

    if request.method == 'POST' and form.validate():
        token = UserReset.query.filter_by(token=form.token.data).one()

        # store encrypted (bcrypt) password
        token.user.password = PasswordHelper.encrypt(form.password.data)
        token.user.updated_at = utcnow()

        logger.info('user password reset, token accepted, password reset for user {}'.format(token.user.username))

        db_session.delete(token)
        db_session.commit()
        return redirect(url_for('frontend.login'))

    return render_template('user/reset2.html', form=form)

@blueprint.route('/settings', methods=['GET', 'POST'])
def settings():
    form = SettingsForm(request.form, obj=Struct(**session['settings']))
    if request.method == 'POST' and form.validate():
        if 'reset' in request.form:
            session['settings'] = SessionHelper.get_settings(True)
            form = SettingsForm(None, obj=Struct(**session['settings']))
        else:
            session['settings'] = dict_merge(SessionHelper.get_settings(), form.data)
        user = SessionHelper.get_user_model()
        if user:
            user.settings = SessionHelper.get_settings_string()
            user.updated_at = utcnow()
            db_session.add(user)
            db_session.commit()
        return redirect(url_for('frontend.paste_index'))

    return render_template('settings.html', form=form)

@blueprint.route('/stats.json')
def stats_json():
    stats = {}
    # paste facts:
    def pastes_by_language():
        return db_session\
                .query(Paste.language, func.count(Paste.language))\
                .group_by(Paste.language).all()

    stats['pastes'] = {
        'all': Paste.query.count(),
        'private': Paste.query.filter_by(private=True).count(),
        'encrypted': Paste.query.filter_by(encrypted=True).count(),
        'language': dict(pastes_by_language()),
    }
    stats['users'] = {
        'all': User.query.count(),
    }
    return jsonify(**stats)

