
from test import app, client
from pprint import PrettyPrinter
pprint = PrettyPrinter(indent=4).pprint

from unittest import TestCase
class UserTestCase(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_sign_up(self):
        rv = client.get('/signup')
        assert 'Sign Up' in rv.data

        rv = self._signup('test', 'test')
        # redirects to Login page = no error occured:
        assert 'Login' in rv.data
        rv = self._login('test', 'test')
        self.assertRegexpMatches(rv.data, r'logged in as <[^>]+>test')

        # wrong confirm:
        rv = self._post('/signup', username='a', password='b', confirm='c')
        assert 'Passwords must match' in rv.data

    def _signup(self, username, password):
        return self._post('/signup', username=username, password=password, confirm=password)

    def _login(self, username, password):
        return self._post('/login', username=username, password=password)

    def _post(self, url, **kwargs):
        return client.post(url, data=kwargs, follow_redirects=True)


