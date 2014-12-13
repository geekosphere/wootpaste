from pygments.lexers import get_all_lexers, get_lexer_by_name, guess_lexer
from pygments.styles import get_all_styles
from pygments.formatters import HtmlFormatter
from pygments.styles import get_style_by_name
from pygments import highlight

from flask import session

from helpers import PasteHelper

class ViewFilters(object):
    @staticmethod
    def register(app):
        # create this using reflection?
        app.jinja_env.filters['highlight'] = ViewFilters.highlight
        app.jinja_env.filters['format_date'] = ViewFilters.format_date
        app.jinja_env.filters['language_display_name'] = ViewFilters.language_display_name
        app.jinja_env.filters['has_permission'] = ViewFilters.has_permission

    @staticmethod
    def format_date(date):
        #return date.strftime('%d.%m.%Y %H:%M %Z')
        return date.strftime('%Y-%m-%d %H:%M %Z')

    @staticmethod
    def language_display_name(language, code):
        if language == 'auto':
            lexer = guess_lexer(code)
        else:
            lexer = get_lexer_by_name(language)
        if lexer:
            # returns the human readable name of this lexer:
            return lexer.name
        else:
            return 'Unknown'

    @staticmethod
    def highlight(code, language):
        if language == 'auto':
            try:
                lexer = guess_lexer(code, stipall=True)
            except:
                lexer = get_lexer_by_name('text', stripall=True)
        else:
            lexer = get_lexer_by_name(language, stripall=True)
        formatter = HtmlFormatter(style=session['settings']['pygment_style'],
                linenos=session['settings']['pygment_linenos'], cssclass="source")
        return highlight(code, lexer, formatter)

    @staticmethod
    def has_permission(paste):
        return PasteHelper.has_permission(paste)

