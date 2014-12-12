# -*- coding: utf-8 -*-

import yaml
import os
import logging.config

from wootpaste.utils import dict_merge

class ConfigAccessor(object):
    def __init__(self, local='local.yaml'):
        self._data = self.load('config.yaml')
        local = self.load(local)
        self._data = dict_merge(self._data, local)

    def load(self, filename):
        filename = self.path(filename)
        if not os.path.isfile(filename): return {}
        with open(filename, 'r') as f:
            return yaml.load(f.read())

    def path(self, filename):
        root = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(root, '..', filename)

    def __getitem__(self, key):
        """Allows to use dot syntax in array accessor operator [] for read access.
        
        Like ``config['database.uri']`` to access ``self._data['database']['uri']``.
        """
        return reduce(lambda d, k: d[k], key.split('.'), self._data)


# initialize module global instance of Configuration (unloaded):
if os.environ.get('ENV', None) == 'test':
    config = ConfigAccessor('test/_config.yaml')
else:
    config = ConfigAccessor()

# initialize logging based on configuation
logging.config.dictConfig(config['logger'])

