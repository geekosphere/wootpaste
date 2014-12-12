\#wootpaste
===========

This is the source code for the [paste.geekosphere.org](https://paste.geekosphere.org) pastebin. It is strong-copyleft licensed under the Affero General Public License Version 3.

## Dependencies

If you intent to use the wootpaste software, first make sure you're not an idiot. When you finished making sure not beeing an idiot, install the required dependencies:

* PostgreSQL
* Python 2.7
* All python modules listed in `requirements.txt`:
    * Flask
    * Flask-WTF
    * Jinja2
    * SQLAlchemy
    * alembic
    * psycopg2
    * PyYAML
    * Pygments
    * passlib

### VirtualEnv/PIP

Its a good idea to setup virtualenv and virtualenv-wrapper to use a local environment for the python modules:

```
% mkvirtualenv wootpaste
% workon wootpaste
% pip install -r requirements.txt
```

### nginx/uwsgi

...

## Testing

```
pip install nose
nosetests test
```


