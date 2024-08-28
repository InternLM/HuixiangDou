import logging

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            '()': 'uvicorn.logging.DefaultFormatter',
            'fmt': '%(levelprefix)s %(asctime)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'default': {
            'formatter': 'default',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stderr',
        },
    },
    'loggers': {
        'uvicorn': {
            'handlers': ['default'],
            'level': 'INFO'
        },
        'uvicorn.error': {
            'level': 'INFO'
        },
        'uvicorn.access': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': False
        },
    },
}
