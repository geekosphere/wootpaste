# -*- coding: utf-8 -*-

import string
import random
import json
import re
import os
import codecs
from uuid import uuid4
from pygments.lexers import get_all_lexers, get_lexer_by_name, guess_lexer
from pygments.styles import get_all_styles
from pygments.formatters import HtmlFormatter
from pygments.styles import get_style_by_name
from pygments import highlight

from wootpaste.database import db_session
from wootpaste.models import *
from wootpaste.utils import dict_merge
from wootpaste.config import config

from flask import g, session
from passlib.context import CryptContext

from jinja2 import Template

import requests

def get_token(length):
    return ''.join([random.choice(string.ascii_letters+string.digits)
            for i in xrange(length)])

class PasteHelper(object):
    @staticmethod
    def get_free_key(private=False, xkcd=False):
        if xkcd:
            token_fn = PasteHelper.get_xkcd_token
            length = 4 if private else 2
        else:
            token_fn = get_token
            length = 18 if private else 2

        key = token_fn(length)
        while Paste.query.filter_by(key=key).count() > 0:
            key = token_fn(length)
            length += 1
        return key

    @staticmethod
    def get_xkcd_token(length):
        if not hasattr(PasteHelper, 'wordlist'):
            filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    '../../wordlist')
            with open(filename, 'r') as f:
                PasteHelper.wordlist = f.read().split('\n')
        return '-'.join([random.choice(PasteHelper.wordlist) for x in xrange(0, length)])

    @staticmethod
    def get_secret():
        return get_token(48)

    @staticmethod
    def get_languages():
        langs = [('auto', 'Auto-detect'), ('text', 'Text (no highlight)')]
        lexers = list(get_all_lexers())
        # case-insensitive sorting
        lexers = sorted(lexers, key=lambda s: s[0].lower())
        for longname, shortnames, ext, mime in lexers:
            if shortnames[0] == 'text': continue
            langs.append((shortnames[0], longname))

        primary = config['paste.primary_languages']
        first = filter(lambda l: l[0] in primary, langs)
        rest = filter(lambda l: l[0] not in primary, langs)
        return first + rest

    @staticmethod
    def get_all_styles():
        return [(x,x) for x in get_all_styles()]

    @staticmethod
    def get_style(style):
        formatter = HtmlFormatter(style=style, linenos=True, cssclass="source")
        return str(formatter.get_style_defs(['.source_container']))

    @staticmethod
    def add_paste_visit(paste):
        paste_expired = False
        session_id = SessionHelper.get_session_id(session)
        if not PasteVisit.query.filter_by(session=session_id, paste_id=paste.id).count():
            pv = PasteVisit()
            pv.paste_id = paste.id
            pv.session = session_id
            paste.visits += 1
            if paste.expire_views != None and paste.expire_views > 1 and paste.visits > paste.expire_views: 
                paste_expired = True
                db_session.delete(paste)
            else:
                db_session.add(pv)

        db_session.commit()
        return paste_expired

    @staticmethod
    def irc_announce(paste):
        message = ''
        template = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../views/irc_announce')
        with codecs.open(template, 'r', 'utf-8') as f:
            message = re.sub(r'\s{2,}', u' ', Template(f.read()).render(paste=paste))

        c = config['irc_announce']
        requests.post(c['uri'], data={
            'username': c['username'], 'password': c['password'],
            'command': 'say %s %s' % (c['channel'], message)})

    @staticmethod
    def has_permission(paste):
        if g.is_admin: return True
        if paste.owner_session == SessionHelper.get_session_id(session): return True
        if g.user and paste.owner_user_id == g.user.id: return True
        return False

class SessionHelper(object):
    @staticmethod
    def get_session_id(session):
        if not 'sid' in session:
            session['sid'] = str(uuid4())
        return session['sid']

    @staticmethod
    def get_user_model():
        if 'username' in session:
            res = User.query.filter_by(username=session['username'])
            if res.count():
                return res.one()

    @staticmethod
    def get_settings(resetDefaults=False):
        """
        Return default settings,
           session settings merged with defaults or
               user settings merged with defaults.
        """

        # default settings: this might introduce new settings!
        settings = {
                'ace': False,
                'pygment_style': 'trac',
                'pygment_linenos': False,
                }

        if resetDefaults:
            return settings

        # user settings merge with defaults:
        user = SessionHelper.get_user_model()
        if user:
            settings = dict_merge(settings, json.loads(user.settings))

        # session settings aswell:
        if 'settings' in session:
            settings = dict_merge(settings, session['settings'])

        return settings

    @staticmethod
    def get_settings_string():
        return json.dumps(session['settings'])


class PasswordHelper(object):
    context = CryptContext(
        schemes=["bcrypt", "pbkdf2_sha512"],
        default="bcrypt",
        all__vary_rounds = 0.1,
        # *aluhut aufsetz*
        bcrypt__default_rounds = 14, # 2^n
        pbkdf2_sha256__default_rounds = 80000,
    )

    @staticmethod
    def encrypt(plain):
        return PasswordHelper.context.encrypt(plain)

    @staticmethod
    def verify(plain, hash):
        return PasswordHelper.context.verify(plain, hash)

