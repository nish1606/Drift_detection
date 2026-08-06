from __future__ import annotations

import logging
import sys
from logging.config import dictConfig


def configure_logging(level: str = "INFO") -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                }
            },
            "handlers": {
                "stdout": {
                    "class": "logging.StreamHandler",
                    "stream": sys.stdout,
                    "formatter": "standard",
                }
            },
            "root": {"handlers": ["stdout"], "level": level.upper()},
        }
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
