
import sys
import os

os.environ['ENV'] = 'test'

from os.path import join, dirname, abspath, realpath
sys.path.append(realpath(join(dirname(abspath(__file__)), '..')))

from wootpaste.app import create_app
from wootpaste.database import engine, db_session, Base

app = create_app()
client = app.test_client()

def setUpPackage():
    Base.metadata.create_all(bind=engine)

def tearDownPackage():
    pass

