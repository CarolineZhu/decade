#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Curtis Yu
@contact: cuyu@splunk.com
@since: 13/12/2017
"""
import logging
import sys
from colorama import Fore, Back, Style

# Python 2+3 compatibility settings for logger
bytes_type = bytes
if sys.version_info >= (3,):
    unicode_type = str
    basestring_type = str
    xrange = range
else:
    # The names unicode and basestring don't exist in py3 so silence flake8.
    unicode_type = unicode  # noqa
    basestring_type = basestring  # noqa


def _safe_unicode(s):
    try:
        if isinstance(s, (unicode_type, type(None))):
            return s
        if not isinstance(s, bytes):
            raise TypeError(
                "Expected bytes, unicode, or None; got %r" % type(s))
        return s.decode("utf-8")
    except UnicodeDecodeError:
        return repr(s)


class LogFormatter(logging.Formatter):
    """
    Log formatter used in Tornado. Key features of this formatter are:
    * Color support when logging to a terminal that supports it.
    * Timestamps on every log line.
    * Robust against str/bytes encoding problems.
    """
    DEFAULT_FORMAT = '%(color)s[%(asctime)s] %(levelname)1.1s - %(name)s%(empty)s| %(end_color)s %(message)s'
    DEFAULT_DATE_FORMAT = '%y-%m-%d %H:%M:%S'
    DEFAULT_STYLES = {
        logging.DEBUG: Style.NORMAL,
        logging.INFO: Style.NORMAL,
        logging.WARNING: Style.BRIGHT,
        logging.ERROR: Style.BRIGHT,
        logging.CRITICAL: Style.BRIGHT,
    }

    def __init__(self,
                 color,
                 fmt=DEFAULT_FORMAT,
                 datefmt=DEFAULT_DATE_FORMAT):
        r"""
        :arg bool color: Enables color support.
        :arg string fmt: Log message format.
          It will be applied to the attributes dict of log records. The
          text between ``%(color)s`` and ``%(end_color)s`` will be colored
          depending on the level if color support is on.
        :arg dict colors: color mappings from logging level to terminal color
          code
        :arg string datefmt: Datetime format.
          Used for formatting ``(asctime)`` placeholder in ``prefix_fmt``.
        .. versionchanged:: 3.2
           Added ``fmt`` and ``datefmt`` arguments.
        """
        logging.Formatter.__init__(self, datefmt=datefmt)
        self._color = color
        self._fmt = fmt
        self._normal = Style.RESET_ALL

    def format(self, record):
        try:
            message = record.getMessage()
            assert isinstance(message,
                              basestring_type)  # guaranteed by logging
            # Encoding notes:  The logging module prefers to work with character
            # strings, but only enforces that log messages are instances of
            # basestring.  In python 2, non-ascii bytestrings will make
            # their way through the logging framework until they blow up with
            # an unhelpful decoding error (with this formatter it happens
            # when we attach the prefix, but there are other opportunities for
            # exceptions further along in the framework).
            #
            # If a byte string makes it this far, convert it to unicode to
            # ensure it will make it out to the logs.  Use repr() as a fallback
            # to ensure that all byte strings can be converted successfully,
            # but don't do it by default so we don't add extra quotes to ascii
            # bytestrings.  This is a bit of a hacky place to do this, but
            # it's worth it since the encoding errors that would otherwise
            # result are so useless (and tornado is fond of using utf8-encoded
            # byte strings wherever possible).
            record.message = _safe_unicode(message)
        except Exception as e:
            record.message = "Bad message (%r): %r" % (e, record.__dict__)

        record.asctime = self.formatTime(record, self.datefmt)

        if record.levelno in self.DEFAULT_STYLES:
            record.color = self.DEFAULT_STYLES[record.levelno] + self._color
            record.end_color = self._normal
        else:
            record.color = record.end_color = ''

        space_number = 12 - len(record.name)
        record.empty = '' if space_number <= 0 else ' ' * space_number

        formatted = self._fmt % record.__dict__

        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            # exc_text contains multiple lines.  We need to _safe_unicode
            # each line separately so that non-utf8 bytes don't cause
            # all the newlines to turn into '\n'.
            lines = [formatted.rstrip()]
            lines.extend(
                _safe_unicode(ln) for ln in record.exc_text.split('\n'))
            formatted = '\n'.join(lines)
        return formatted.replace("\n", "\n    ")


def setup_logger(name=None, color=None, level=logging.DEBUG):
    _logger = logging.getLogger(name or __name__)
    _logger.propagate = False
    _logger.setLevel(level)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(LogFormatter(color))
    _logger.addHandler(stream_handler)

    return _logger


if __name__ == '__main__':
    from colorama import init
    init()
    logger = setup_logger('TestLogger', color=Fore.BLUE)
    logger.info('hello')
    logger.error('errrrr')
