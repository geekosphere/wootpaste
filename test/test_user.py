# -*- coding: utf-8 -*-

import test
import re
from test import AppTestCase
import flask
from wootpaste import mail

class UserTestCase(AppTestCase):

    def test_sign_up(self):
        with self.app.test_client() as c:
            assert 'Sign Up' in c.get('/signup').data
            rv = c.post('/signup', data=dict(username='foo', password='bar', confirm='bar'))
            assert 'login' in rv.data
            assert 'error' not in rv.data

            rv = c.post('/login', data=dict(username='foo', password='bar'), follow_redirects=True)
            self.assertRegexpMatches(rv.data, r'logged in as <[^>]+>foo')

    def test_sign_up_confirm_error(self):
        with self.app.test_client() as c:
            rv = c.post('/signup', data=dict(username='foo', password='bar', confirm='baz'))
            assert 'Passwords must match' in rv.data

    def test_sign_up_duplication_error(self):
        with self.app.test_client() as c:
            rv = c.post('/signup', data=dict(username='dupl', password='bar', confirm='bar'))
            assert 'Username already taken!' not in rv.data
            rv = c.post('/signup', data=dict(username='dupl', password='bar', confirm='bar'))
            print rv.data
            assert 'Username already taken!' in rv.data

    def test_password_reset(self):
        with mail.record_messages() as outbox:
            with self.app.test_client() as c:
                rv = c.post('/signup', data=dict(username='josh', password='foo', confirm='foo', email='josh@momcorp.com'))
                # test login:
                rv = c.post('/login', data=dict(username='josh', password='foo'), follow_redirects=True)
                self.assertRegexpMatches(rv.data, r'logged in as <[^>]+>josh')
                # request password reset
                rv = c.post('/reset', data=dict(username='josh'))
                assert '/reset2' in rv.data

            # check the sent reset email:
            reset_mail = outbox[-1]
            assert 'josh@momcorp.com' in reset_mail.recipients
            assert 'Password Reset - wootpaste' in reset_mail.subject
            assert 'Or use this token' in reset_mail.body
            m = re.findall(r'Or use this token: (\S+)', reset_mail.body)
            assert len(m) == 1
            token = m[0]

            with self.app.test_client() as c:
                # change password:
                rv = c.post('/reset2', data=dict(token=token, password='bar', confirm='bar'))
                # test login:
                rv = c.post('/login', data=dict(username='josh', password='bar'), follow_redirects=True)
                self.assertRegexpMatches(rv.data, r'logged in as <[^>]+>josh')

    def test_password_reset_user_without_email(self):
        with mail.record_messages() as outbox:
            with self.app.test_client() as c:
                rv = c.post('/signup', data=dict(username='peter', password='foo', confirm='foo'))
                # test login:
                rv = c.post('/login', data=dict(username='peter', password='foo'), follow_redirects=True)
                self.assertRegexpMatches(rv.data, r'logged in as <[^>]+>peter')
                # request password reset
                rv = c.post('/reset', data=dict(username='peter'))
                assert 'Email not set!' in rv.data

            assert len(outbox) == 0

    def test_password_reset_user_wrong_token(self):
        with mail.record_messages() as outbox:
            with self.app.test_client() as c:
                rv = c.post('/signup', data=dict(username='willow', password='foo', confirm='foo', email='josh@momcorp.com'))
                rv = c.post('/reset', data=dict(username='willow'))
                assert '/reset2' in rv.data
                rv = c.post('/reset2', data=dict(token='not the token', password='bar', confirm='bar'))
                assert 'Invalid token!' in rv.data
                rv = c.post('/login', data=dict(username='willow', password='bar'))
                assert 'wrong password' in rv.data


