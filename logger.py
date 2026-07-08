"""Central logger configuration for the Kung Fu Chess engine.

Import `logger` from this module in any file that needs logging.
Log output goes to stderr so it does not interfere with stdout (board prints).

Usage:
    from logger import logger
    logger.debug("piece selected at %s", pos)
"""

import logging
import sys

logging.basicConfig(
    stream=sys.stderr,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger("chess")
