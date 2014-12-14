# -*- coding: utf-8 -*-

from unittest import TestCase
import os

os.environ['ENV'] = 'test'

from wootpaste.app import create_app
from wootpaste.database import engine, Base

class AppTestCase(TestCase):

    @classmethod
    def setup_class(klass):
        Base.metadata.create_all(bind=engine)
        klass.app = create_app()

