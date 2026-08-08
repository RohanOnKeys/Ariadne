"""
utils.logging

Logger setup honouring `LOG_LEVEL` (see `ariadne.config.settings`). Call
`get_logger(__name__)` from any module instead of configuring logging
directly, so every module's output goes through one consistent format
and level.
"""

import logging

from ariadne.config.settings import LOG_LEVEL

_configured = False


def _configure_root() -> None:
    global _configured
    if _configured:
        return

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
    ))

    root = logging.getLogger("ariadne")
    root.addHandler(handler)
    root.setLevel(LOG_LEVEL)
    root.propagate = False

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Return a module logger under the `ariadne` namespace, configured to
    honour `LOG_LEVEL`.

    Args:
        name: logger name, typically the caller's `__name__`.

    Returns:
        A `logging.Logger` ready to use.
    """
    _configure_root()
    return logging.getLogger(name)
