# -*- coding: utf-8 -*-

import test
import re
from test import AppTestCase
import flask
from wootpaste import mail
from wootpaste.database import db_session
from wootpaste.models import Paste

class PasteTestCase(AppTestCase):

    def test_create_guest(self):
        with self.app.test_client() as c:
            rv = c.post('/', data=dict(title='Linux sysLog Messages', content='bar', language='auto'), follow_redirects=True)
            self.assertRegexpMatches(rv.data, r'<h1>\s+Linux sysLog Messages\s+</h1>')

            # should appear in the public list
            rv = c.get('/list')
            self.assertRegexpMatches(rv.data, r'<h2><a href="/paste/[^"]+" title="[^"]+">Linux sysLog Messages</a></h2>')

    def test_spam(self):
        # as a guest:
        with self.app.test_client() as c:
            # filled invisible field:
            rv = c.post('/', data=dict(title='foo', content='foo', subject='bar', language='auto'), follow_redirects=True)
            assert 'detected as spam' in rv.data

            # strange title:
            rv = c.post('/', data=dict(title='QZUyVyetKEPQNOa', content='foo', language='auto'), follow_redirects=True)
            assert 'detected as spam' in rv.data

        # posted privatly:
        with self.app.test_client() as c:
            rv = c.post('/', data=dict(title='QZUyVyetKEPQNOa', content='foo', language='auto', private='t'), follow_redirects=True)
            self.assertRegexpMatches(rv.data, r'<h1>\s+QZUyVyetKEPQNOa\s+</h1>')

        # as a logged-in user:
        with self.app.test_client() as c:
            c.post('/signup', data=dict(username='spamtest', password='bar', confirm='bar'))
            c.post('/login', data=dict(username='spamtest', password='bar'), follow_redirects=True)

            rv = c.post('/', data=dict(title='QZUyVyetKEPQNOa', content='foo', language='auto'), follow_redirects=True)
            self.assertRegexpMatches(rv.data, r'<h1>\s+QZUyVyetKEPQNOa\s+</h1>')

    def test_spam_field(self):
        db_session.add(Paste(key='spam_field_test', content='foobar', spam=False))
        db_session.commit()
        with self.app.test_client() as c:
            assert 'foobar' in c.get('/list').data

        db_session.add(Paste(key='spam_field_test2', content='foobar2', spam=True))
        db_session.commit()
        with self.app.test_client() as c:
            assert 'foobar2' not in c.get('/list').data

        # the spam marker has no other effects anywhere else



