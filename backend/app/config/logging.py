import logging
import logging.config
import sys
from typing import Any

from app.config.settings import settings

LOGGING_CONFIG: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        },
        "access": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": sys.stdout,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": logging.DEBUG if settings.DEBUG else logging.INFO,
    },
    "loggers": {
        "uvicorn": {"handlers": ["console"], "level": logging.INFO, "propagate": False},
        "uvicorn.error": {"handlers": ["console"], "level": logging.INFO, "propagate": False},
        "uvicorn.access": {"handlers": ["console"], "level": logging.INFO, "propagate": False},
        "sqlalchemy.engine": {
            "handlers": ["console"],
            "level": logging.WARNING,
            "propagate": False,
        },
    },
}


def setup_logging() -> None:
    logging.config.dictConfig(LOGGING_CONFIG)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
