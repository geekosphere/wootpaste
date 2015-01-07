# -*- coding: utf-8 -*-

from wootpaste.utils.helpers import *
from wootpaste.config import config
from wootpaste.models import *

from flask_wtf import Form
from wtforms import *
from wtforms.validators import *
from datetime import timedelta
import datetime

class SpamDetected(ValidationError):
    def __init__(self):
        ValidationError.__init__(self, 'The paste you submitted was detected as spam, if this is a false positive, try to login or paste it privatly.')

class SignupForm(Form):
    def username_free_check(form, field):
        if User.query.filter_by(username=field.data).count():
            raise ValidationError('Username already taken!')

    username = StringField(u'Username', validators=[InputRequired(), length(max=30), username_free_check, Regexp(r'^[a-zA-Z0-9_\-]{2,}$')])
    password = PasswordField('Password', validators=[InputRequired(), EqualTo('confirm', message='Passwords must match')])
    confirm  = PasswordField('Confirm Password')
    email = StringField(u'eMail (optional)', validators=[Email(), optional(), length(max=1024)])

class LoginForm(Form):
    def password_check(form, field):
        user = User.query.filter_by(username=form.username.data)
        if not user.count() or not PasswordHelper.verify(field.data, user.one().password):
            raise ValidationError('User not found or wrong password!')

    username = StringField(u'Username', validators=[InputRequired(), length(max=30)])
    password = PasswordField('Password', validators=[InputRequired(), password_check])

class PasswordResetForm(Form):
    def username_exists_check(form, field):
        query = User.query.filter(User.username == form.username.data)
        if not query.count():
            raise ValidationError('User not found!')
        if not query.one().email:
            raise ValidationError('Email not set! Contact sysadmin to reset.')

    username = StringField(u'Username', validators=[InputRequired(), username_exists_check])

class PasswordResetTokenForm(Form):
    def valid_token_check(form, field):
        query = UserReset.query.filter_by(token=form.token.data)
        if not query.count():
            raise ValidationError('Invalid token!')

    token = StringField(u'Token', validators=[InputRequired(), valid_token_check])
    password = PasswordField('New Password', validators=[InputRequired(), EqualTo('confirm', message='Passwords must match')])
    confirm  = PasswordField('Confirm Password')

class SettingsForm(Form):
    ace = BooleanField(u'ace editor')
    pygment_style = SelectField(u'Pygments style:', choices=PasteHelper.get_all_styles())
    pygment_linenos = BooleanField(u'Line numbers')
    show_qrcode = BooleanField(u'show qrcode')

class PasteForm(Form):
    def valid_encryption_check(form, field):
        if field.data and not re.match(r'^[\w{}":,+/=]+$', form.content.data):
            raise ValidationError('Invalid encrypted content!')

    def spam_check(form, field):
        # no spam detection for registered users or private pastes:
        if form.private.data or g.user:
            return

        # invisible field was filled-in (by a bot)
        if request.form.get('subject', '') != '':
            raise SpamDetected()

        # check for random pattern in title:
        if re.match(r'(\w*[A-Z][a-z]\w*|\w*[a-z][A-Z]\w*){2}', form.title.data):
            raise SpamDetected()

    private = BooleanField(u'private')
    irc_announce = BooleanField(u'announce')
    encrypted = BooleanField(u'client-side encrypted', validators=[valid_encryption_check])
    expire_in = SelectField(u'expire in', choices=[
        (0, 'never'),
        (int(timedelta(minutes=30).total_seconds()), 'half an hour'),
        (int(timedelta(hours=1).total_seconds()), 'one hour'),
        (int(timedelta(hours=3).total_seconds()), 'three hours'),
        (int(timedelta(hours=6).total_seconds()), 'six hours'),
        (int(timedelta(hours=12).total_seconds()), 'twelve hours'),
        (int(timedelta(days=1).total_seconds()), 'one day'),
        (int(timedelta(weeks=1).total_seconds()), 'a week'),
        (int(timedelta(weeks=4).total_seconds()), 'one month'),
        (int(timedelta(weeks=4*3).total_seconds()), 'three months'),
        (int(timedelta(weeks=4*6).total_seconds()), 'six months'),
        (int(timedelta(days=365).total_seconds()), 'a year'),
        (int(timedelta(days=365*2).total_seconds()), 'two years')], coerce=int,
        validators=[optional()])
    expire_views = SelectField(u'expire after', choices=[
        (0, 'never'),
        (2, '2 views'),
        (3, '3 views'),
        (4, '4 views'),
        (5, '5 views'),
        (10, '10 views'),
        (50, '50 views'),
        (1000, '1000 views'),
        ], coerce=int, validators=[optional()])
    title = StringField(u'Title', validators=[optional(), length(max=1024)])
    content = TextAreaField(u'Content', validators=[required(), spam_check])
    language = SelectField(u'Language', choices=PasteHelper.get_languages())
    xkcd_ids = BooleanField(u'xkcd-style ids')
    owner_user_hidden = BooleanField(u'post anonymous')

