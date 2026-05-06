"""Logging configuration for the M&A research pipeline.
Import in any entry-point script to enable debug logging."""
import logging
import sys


def configure_logging(level=logging.INFO, log_file=None):
    """Configure pipeline logging. By default logs to stderr.
    
    Args:
        level: logging.DEBUG, INFO, WARNING, etc.
        log_file: optional path to write logs (in addition to stderr)
    """
    handlers = [logging.StreamHandler(sys.stderr)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
        datefmt='%H:%M:%S',
        handlers=handlers,
        force=True,
    )
