
class WootpasteError(Exception):
    pass

class PasteExpired(WootpasteError):
    status_code = 500

    def __init__(self):
        Exception.__init__(self)
        self.message = 'Paste expired.'

    def to_dict(self):
        # rv = dict(self.payload or ())
        rv = {}
        rv['message'] = self.message
        return rv

class SpamDetected(WootpasteError):
    status_code = 500

    def __init__(self):
        Exception.__init__(self)
        self.message = 'This is spam go fuck yourself!'

    def to_dict(self):
        # rv = dict(self.payload or ())
        rv = {}
        rv['message'] = self.message
        return rv

class PasteNotFound(WootpasteError):
    status_code = 500

    def __init__(self):
        Exception.__init__(self)
        self.message = 'Paste not found.'
        self.status_code = 404

    def to_dict(self):
        # rv = dict(self.payload or ())
        rv = {}
        rv['message'] = self.message
        return rv


