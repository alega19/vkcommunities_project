from .common import *


DEBUG = False

ALLOWED_HOSTS = get_secret('ALLOWED_HOSTS')

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
        'TIMEOUT': None,
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s %(levelname)-8s %(name)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'celery': {
            'format': '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
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
            'encoding': 'utf-8',
        },
        'dbcleaner_file': {
            'level': 'INFO',
            'formatter': 'default',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': '/var/log/vkcommunities/dbcleaner',
            'when': 'H',
            'interval': 1,
            'backupCount': 240,
            'encoding': 'utf-8',
        },
        'celery_file': {
            'level': 'INFO',
            'formatter': 'celery',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': '/var/log/vkcommunities/celery',
            'when': 'H',
            'interval': 1,
            'backupCount': 240,
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        'datacollector': {
            'level': 'INFO',
            'handlers': ['file'],
        },
        'dbcleaner': {
            'level': 'INFO',
            'handlers': ['dbcleaner_file'],
        },
        'celery': {
            'level': 'INFO',
            'handlers': ['celery_file'],
        },
    }
}

STATIC_ROOT = root('static')
