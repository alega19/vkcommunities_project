from .common import *


DEBUG = False

ALLOWED_HOSTS = get_secret('ALLOWED_HOSTS')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s %(levelname)-8s %(name)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'formatter': 'default',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': '/var/log/vkcommunities/datacollector',
            'when': 'H',
            'interval': 1,
            'backupCount': 240,
        },
    },
    'loggers': {
        'datacollector': {
            'level': 'INFO',
            'handlers': ['file'],
        },
    }
}

STATIC_ROOT = root('static')
