from .base import *

BOOKING_ON = True

LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
            }
        },
        'loggers': {
            'django.request': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': True,
            },
            'booking': {
                'handlers': ['console'],
                'level': 'INFO',
                'propogate': True,
            },
            'payments': {
                'handlers': ['console'],
                'level': 'INFO',
                'propogate': True,
            },
            'studioadmin': {
                'handlers': ['console'],
                'level': 'INFO',
                'propogate': True,
            },
            'timetable': {
                'handlers': ['console'],
                'level': 'INFO',
                'propogate': True,
            },
        },
    }

TESTING = True