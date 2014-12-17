# -*- coding: utf-8 -*-

import datetime
import pytz

from flask.ext.script import Manager
from wootpaste.app import create_app
from wootpaste.config import config
from wootpaste.database import db_session
from wootpaste.models import *
from wootpaste.utils import utcnow
if config['paste.spam_ml']:
    import wootpaste.utils.spam_ml as spam_ml

app = create_app()
manager = Manager(app)

import logging
logger = logging.getLogger('wootpaste')

@manager.command
def cleanup():
    """Removes expired pastes and old visit logs from the database.

    Should be called periodically to cleanup the database.
    """
    delete_expired_pastes()
    delete_old_paste_visit()

def delete_expired_pastes():
    deleted= []
    for paste in Paste.query.filter(Paste.expire_in > 0).all():
        if paste.is_expired():
            db_session.delete(paste)
            deleted.append(paste.key)
    db_session.commit()
    if len(deleted) > 0: logger.info('delete {} expired pastes: {}'.format(len(deleted), ', '.join(deleted)))

def delete_old_paste_visit():
    num = 0
    for visit in PasteVisit.query.filter(PasteVisit.created_at < utcnow() - timedelta(hours=6)).all():
        num+=1
        db_session.delete(visit)
    db_session.commit()
    if num > 0: logger.info('delete {} paste visits'.format(num))

if config['paste.spam_ml']:
    @manager.command
    def spam_evaluate():
        """Evaluates the model used for paste spam detection."""
        print 'Running evaluation... '
        avg = spam.evaluate()
        print 'Average Score: ' + str(avg)

    @manager.command
    def spam_train():
        """Trains the model used for paste spam detection."""
        print 'Training running...'
        spam.train()

if __name__ == "__main__":
    manager.run()

