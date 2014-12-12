# implictly loads the config globally (based on ENV)
import wootpaste.config
from flask.ext.mail import Mail

mail = Mail()

