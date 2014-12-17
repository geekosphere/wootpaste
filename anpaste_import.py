#!/usr/bin/env python
# import anpaste sqlite database into the sqlalchemy wootpaste database model

ANPASTE_DB = './anpaste.sqlite'

import sys
import sqlite3
import datetime
import traceback


from wootpaste.database import db_session
from wootpaste.models import Paste
from wootpaste.blueprint.forms import PasteForm
from wootpaste.utils.helpers import PasteHelper, SessionHelper

language_lexer = {
'as3': 'as3',
'bash': 'bash',
'clojure': 'clojure',
'cpp': 'cpp',
'css': 'css',
'java': 'java',
'jscript': 'js',
'lua': 'lua',
'perl': 'perl',
'php': 'php',
'plain': 'text',
'python': 'python',
'ruby': 'rb',
'sql': 'sql',
'tcl': 'tcl',
'xml': 'xml',
'yaml': 'yaml',
}

def to_bool(x):
    return True if x == 1 else False

def process_paste(old):
    keys = ('id', 'secret', 'username', 'summary', 'content', 'expire', 'created', 'encrypted', 'language', 'private', 'status')
    opaste = dict(zip(keys, old))
    try:
        nkey = opaste['id']
        if opaste['status'] == 2:
            nkey = 'spam_' + nkey
        if Paste.query.filter_by(key=nkey).count() > 0:
            print 'ignored existing paste with id='+nkey
            return

        npaste = Paste()
        npaste.spam = opaste['status'] == 2
        npaste.key = nkey
        npaste.legacy = True
        npaste.secret = opaste['secret']
        npaste.private = to_bool(opaste['private'])
        npaste.encrypted = to_bool(opaste['encrypted'])
        if not opaste['summary']:
            npaste.title = None
        else:
            npaste.title = opaste['summary'][:1000]
        npaste.content = opaste['content']
        npaste.created_at = datetime.datetime.utcfromtimestamp(opaste['created']/1000)
        olang = opaste['language']
        if olang and olang != '':
            if olang in language_lexer:
                npaste.language = language_lexer[olang]
            else:
                print 'unknown language detected: '+olang
                npaste.language = 'auto'
        else:
            print 'broken language detected'
            npaste.language = 'auto'
        db_session.add(npaste)
        print 'added paste with old id=' + npaste.key + ' created_at:'+str(npaste.created_at)
    except:
        traceback.print_exc()
        print 'unable to create old id=' + opaste['id']

old = sqlite3.connect(ANPASTE_DB)
map(process_paste, old.execute('SELECT * FROM paste'))
db_session.commit()

