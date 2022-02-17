
  
import logging
import time

from django.http import HttpRequest

from gunicorn import glogging


def get_milliseconds_now():
    return int(time.time() * 1000)


class IgnoreCheckUrl(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        return not ("GET /check/" in message and "200" in message)


class CustomGunicornLogger(glogging.Logger):
    def setup(self, cfg):
        super().setup(cfg)

        # Add filters to Gunicorn logger
        logger = logging.getLogger("gunicorn.access")
        logger.addFilter(IgnoreCheckUrl())