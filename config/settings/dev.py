from .common import *


DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS += [
    'debug_toolbar',
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
] + MIDDLEWARE

INTERNAL_IPS = ['127.0.0.1']

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
        'console': {
            'level': 'INFO',
            'formatter': 'default',
            'class': 'logging.StreamHandler',
        },
        'celery_console': {
            'level': 'INFO',
            'formatter': 'celery',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'datacollector': {
            'level': 'INFO',
            'handlers': ['console'],
        },
        'dbcleaner': {
            'level': 'INFO',
            'handlers': ['console'],
        },
        'celery': {
            'level': 'INFO',
            'handlers': ['celery_console'],
        },
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
