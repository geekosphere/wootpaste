# -*- coding: utf-8 -*-

from wootpaste.config import config
from wootpaste.database import Base

from sqlalchemy import Table, Column, ForeignKey, Integer, String, Text, Boolean, DateTime, TypeDecorator
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
import datetime
import pytz

class UTCDateTime(TypeDecorator):
    impl = DateTime
    def process_result_value(self, value, engine):
        #s = 'notz'
        #if value:
        #    s = value.tzname()
        #print 'process_result_value1 value=[%s]=%s [tz: %s]' % (str(type(value)), str(value), s)
        if value:
            value = pytz.utc.localize(value)
        return value

    def process_bind_param(self, value, engine):
        return value

class Paste(Base):
    __tablename__ = 'paste'

    # auto-increment primary key serial
    id = Column(Integer(), primary_key=True)
    # random alphanumeric string id sequence
    key = Column(String(512), unique=True)
    # owner authentication secret
    secret = Column(String(256))

    created_at = Column(UTCDateTime, default=datetime.datetime.utcnow)
    updated_at = Column(UTCDateTime)

    private = Column(Boolean())
    encrypted = Column(Boolean())

    legacy = Column(Boolean(), default=False)

    # how often the paste was displayed
    view_count = Column(Integer(), default=0)

    # kill-options when this paste should self-destruct
    expire_in = Column(Integer())
    expire_views = Column(Integer())

    title = Column(String(1024))
    content = Column(Text())

    # a pygments lexer type
    language = Column(String(128))

    visits = Column(Integer(), default=0)
    visits_rel = relationship('PasteVisit', cascade='all, delete-orphan')

    # specifies the owner of this paste, grants update/delete permissions
    owner_session = Column(String(40))
    owner_user_id = Column(Integer(), ForeignKey('user.id'))
    owner_user = relationship('User', backref='pastes')

    def must_truncate(self):
        return len(self.content.split('\n')) > config['paste.max_lines']

    def truncate_content(self):
        return '\n'.join(self.content.split('\n')[:config['paste.max_lines']])

class PasteVisit(Base):
    __tablename__ = 'paste_visit'

    paste_id = Column(Integer(), ForeignKey('paste.id'), primary_key=True)
    paste = relationship('Paste')
    session = Column(String(40), primary_key=True)
    created_at = Column(UTCDateTime, default=datetime.datetime.utcnow)

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer(), primary_key=True)

    username = Column(String(30), unique=True)
    email = Column(String(1024), unique=True)
    password = Column(String(2049))

    # admins can manage users, delete pastes, etc.
    admin = Column(Boolean(), default=False)

    # stores a json string with site settings
    settings = Column(Text())

    created_at = Column(UTCDateTime, default=datetime.datetime.utcnow)
    updated_at = Column(UTCDateTime)

class UserReset(Base):
    __tablename__ = 'user_reset'

    token = Column(String(40), primary_key=True)
    user_id = Column(Integer(), ForeignKey('user.id'))
    user = relationship('User')

    created_at = Column(UTCDateTime, default=datetime.datetime.utcnow)


