# wootpaste - python/flask pastebin

This is the source code for the [paste.geekosphere.org](https://paste.geekosphere.org) pastebin, licensed under the [Affero General Public License Version 3](http://www.gnu.org/licenses/agpl-3.0.html). [Affero General Public License](http://www.gnu.org/licenses/agpl-3.0.html), Version 3.

## Install

sass executable needs manual install. (gem install sass)

```
% mkvirtualenv wootpaste
% workon wootpaste
% pip install -r requirements.txt
% python wsgi.py
```

## Testing

```
pip install nose
nosetests test
```

## Database

```
CREATE USER wootpaste WITH PASSWORD 'pw';
CREATE DATABASE wootpaste;
GRANT ALL PRIVILEGES ON DATABASE wootpaste to wootpaste;
```

## Dependencies for spam detection

```
pip install numpy
pip install cython
pip install git+http://github.com/scipy/scipy/
pip install scikit-learn
```

