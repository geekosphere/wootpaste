# -*- coding: utf-8 -*-

import test
import re
from test import AppTestCase
import flask
from wootpaste import mail

class PasteTestCase(AppTestCase):

    def test_create_guest(self):
        with self.app.test_client() as c:
            rv = c.post('/', data=dict(title='Linux sysLog Messages', content='bar', language='auto'), follow_redirects=True)
            self.assertRegexpMatches(rv.data, r'<h1>\s+Linux sysLog Messages\s+</h1>')

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

