
class WootpasteError(Exception):
    pass

class PasteExpired(WootpasteError):
    status_code = 500

    def __init__(self):
        Exception.__init__(self)
        self.message = 'The paste you\'re looking at expired.'

    def to_dict(self):
        # rv = dict(self.payload or ())
        rv = {}
        rv['message'] = self.message
        return rv

class SpamDetected(WootpasteError):
    status_code = 500

    def __init__(self):
        Exception.__init__(self)
        self.message = 'The paste you submitted was detected as spam, if this is a false positive try to login or paste it privatly.'

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


