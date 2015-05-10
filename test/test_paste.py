# -*- coding: utf-8 -*-

import test
import re
from test import AppTestCase
import flask
from wootpaste import mail
from wootpaste.database import db_session
from wootpaste.models import Paste

import logging
logger = logging.getLogger('wootpaste')

class PasteTestCase(AppTestCase):

    def test_create_guest(self):
        with self.app.test_client() as c:
            rv = c.post('/', data=dict(title='Linux sysLog Messages', content='bar', language='auto'), follow_redirects=True)
            self.assertRegexpMatches(rv.data, r'<h1>\s+Linux sysLog Messages\s+</h1>')

            # should appear in the public list
            rv = c.get('/list')
            self.assertRegexpMatches(rv.data, r'<h2><a href="/paste/[^"]+" title="[^"]+">Linux sysLog Messages</a></h2>')

    def test_create_user(self):
        with self.app.test_client() as c:
            c.post('/signup', data=dict(username='nop', password='nop', confirm='nop'))
            c.post('/login', data=dict(username='nop', password='nop'), follow_redirects=True)

            # create a public paste (should list username for this paste)
            rv = c.post('/', data=dict(title='Public Test Paste', content='bar', language='auto'), follow_redirects=True)
            self.assertRegexpMatches(rv.data, r'<h1>\s+Public Test Paste\s+</h1>')
            self.assertRegexpMatches(rv.data, r'by <a href="/user/nop/all"')

    def test_list(self):
        with self.app.test_client() as c:
            c.post('/signup', data=dict(username='tlz', password='nop', confirm='nop'))
            c.post('/login', data=dict(username='tlz', password='nop'), follow_redirects=True)
            c.post('/', data=dict(title='test_list_pub', content='bar', language='auto'), follow_redirects=True)
            c.post('/', data=dict(title='test_list_priv', content='bar', language='auto', private='y'), follow_redirects=True)

            rv = c.get('/user/tlz/all')
            self.assertRegexpMatches(rv.data, r'<h2><[^>]+>test_list_pub<[^>]+></h2>')
            self.assertRegexpMatches(rv.data, r'<h2><[^>]+>test_list_priv<[^>]+></h2>')
            rv = c.get('/user/tlz/private')
            self.assertNotRegexpMatches(rv.data, r'<h2><[^>]+>test_list_pub<[^>]+></h2>')
            self.assertRegexpMatches(rv.data, r'<h2><[^>]+>test_list_priv<[^>]+></h2>')
            rv = c.get('/user/tlz/public')
            self.assertRegexpMatches(rv.data, r'<h2><[^>]+>test_list_pub<[^>]+></h2>')
            self.assertNotRegexpMatches(rv.data, r'<h2><[^>]+>test_list_priv<[^>]+></h2>')

        with self.app.test_client() as c:
            rv = c.get('/user/tlz/all')
            assert 'to target URL: <a href="/user/tlz/public">/user/tlz/public</a>.' in rv.data
            rv = c.get('/user/tlz/private')
            assert 'to target URL: <a href="/user/tlz/public">/user/tlz/public</a>.' in rv.data
            rv = c.get('/user/tlz/public')
            self.assertRegexpMatches(rv.data, r'<h2><[^>]+>test_list_pub<[^>]+></h2>')
            self.assertNotRegexpMatches(rv.data, r'<h2><[^>]+>test_list_priv<[^>]+></h2>')

    def test_owner_hidden(self):
        with self.app.test_client() as c:
            # check no user_hidden checkbox in create form:
            rv = c.get('/')
            assert 'hide username for this paste' not in rv.data

            c.post('/signup', data=dict(username='nop', password='nop', confirm='nop'))
            c.post('/login', data=dict(username='nop', password='nop'), follow_redirects=True)

            # check user_hidden checkbox in create form:
            rv = c.get('/')
            assert 'hide username for this paste' in rv.data

            # create with shown username (should list username for this paste)
            rv = c.post('/', data=dict(title='Hidden Username Test', content='bar', language='auto'), follow_redirects=True)
            self.assertRegexpMatches(rv.data, r'<h1>\s+Hidden Username Test\s+</h1>')
            self.assertRegexpMatches(rv.data, r'by <a href="/user/nop/all"')

            # create with hidden username (should list username for this paste)
            rv = c.post('/', data=dict(title='Hidden Username Test2', content='bar', language='auto', owner_user_hidden='y'), follow_redirects=True)
            self.assertRegexpMatches(rv.data, r'<h1>\s+Hidden Username Test2\s+</h1>')
            self.assertNotRegexpMatches(rv.data, r'by <a href="/user/nop/all"')

            # should be included in user paste list:
            rv = c.get('/user/nop/all')
            self.assertRegexpMatches(rv.data, r'<h2><[^>]+>Hidden Username Test<[^>]+></h2>')
            self.assertRegexpMatches(rv.data, r'<h2><[^>]+>Hidden Username Test2<[^>]+></h2>')

        # the hidden pastes should be excluded for guests:
        with self.app.test_client() as c:
            rv = c.get('/user/nop/public')
            self.assertRegexpMatches(rv.data, r'<h2><[^>]+>Hidden Username Test<[^>]+></h2>')
            self.assertNotRegexpMatches(rv.data, r'<h2><[^>]+>Hidden Username Test2<[^>]+></h2>')

    def test_spam(self):
        # as a guest:
        with self.app.test_client() as c:
            rv = c.post('/', data=dict(title='foo', content='spamtest-123-Q', language='auto'), follow_redirects=True)
            #l print rv.data
            assert 'detected as spam' in rv.data

        # posted privatly should pass spam:
        with self.app.test_client() as c:
            rv = c.post('/', data=dict(title='QZUyVyetKEPQNOa', content='spamtest-123-Q', language='auto', private='t'), follow_redirects=True)
            self.assertRegexpMatches(rv.data, r'<h1>\s+QZUyVyetKEPQNOa\s+</h1>')

        # as a logged-in user should pass spam:
        with self.app.test_client() as c:
            c.post('/signup', data=dict(username='spamtest', password='bar', confirm='bar'))
            c.post('/login', data=dict(username='spamtest', password='bar'), follow_redirects=True)

            rv = c.post('/', data=dict(title='QZUyVyetKEPQNOa', content='spamtest-123-Q', language='auto'), follow_redirects=True)
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

    def test_reg_edit_private(self):
        """Tests if private pastes stay private after editing."""
        with self.app.test_client() as c:
            # create a private paste and get its id:
            rv = c.post('/', data=dict(title='secrets', content='lennart is a dick', language='auto', private='t'), follow_redirects=True)
            key = re.findall(r'href="/paste/([^"]+)"', rv.data)[0]
            logger.info('key = ' + key)

            assert 'private paste' in c.get('/paste/' + key).data
            c.post('/edit/' + key, data=dict(title='secrets', content='systemd for world domination', language='c'))
            assert 'systemd' in c.get('/paste/' + key).data
            assert 'private paste' in c.get('/paste/' + key).data

