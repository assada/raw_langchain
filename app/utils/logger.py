import logging
from logging.config import dictConfig


class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[36m',      # cyan
        'INFO': '\033[32m',       # green
        'WARNING': '\033[33m',    # yellow
        'ERROR': '\033[31m',      # red
        'CRITICAL': '\033[35m',   # magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        record_copy = logging.makeLogRecord(record.__dict__)
        color = self.COLORS.get(record_copy.levelname, '')
        colored_levelname = f'{color}{record_copy.levelname}{self.RESET}:{" " * (7 - len(record_copy.levelname))}'
        record_copy.levelname = colored_levelname
        
        return super().format(record_copy)


def configure_logging() -> None:
    dictConfig(
        {
            'version': 1,
            'disable_existing_loggers': False,
            'filters': {
                'correlation_id': {
                    '()': 'asgi_correlation_id.CorrelationIdFilter',
                    'uuid_length': 8, # TODO: make it dynamic
                    'default_value': '00000000',
                },
            },
            'formatters': {
                'console': {
                    '()': ColoredFormatter,
                    'datefmt': '%H:%M:%S',
                    'format': '%(levelname)s\t\b%(asctime)s %(name)s:%(lineno)d [%(correlation_id)s] %(message)s',
                },
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'filters': ['correlation_id'],
                    'formatter': 'console',
                },
            },
            'loggers': {
                'app': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': True},
                'databases': {'handlers': ['console'], 'level': 'WARNING'},
                'httpx': {'handlers': ['console'], 'level': 'INFO'},
                'asgi_correlation_id': {'handlers': ['console'], 'level': 'WARNING'},
                'uvicorn': {'handlers': ['console'], 'level': 'INFO'},
                'uvicorn.error': {'handlers': ['console'], 'level': 'INFO'},
                'uvicorn.access': {'handlers': ['console'], 'level': 'INFO'},
            },
        }
    )

setup_logger = configure_logging
