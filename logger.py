"""Central logger configuration for the Kung Fu Chess engine.

Import `logger` from this module in any file that needs logging.
Log output goes to stderr so it does not interfere with stdout (board prints).

Usage:
    from logger import logger
    logger.debug("piece selected at %s", pos)
"""

import logging
import sys

_handler = logging.StreamHandler(sys.stderr)
_handler.setFormatter(logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
))

logger = logging.getLogger("chess")
logger.setLevel(logging.DEBUG)
logger.addHandler(_handler)
logger.propagate = False  # don't leak to the root logger — avoids configuring third-party loggers (e.g. websockets)
