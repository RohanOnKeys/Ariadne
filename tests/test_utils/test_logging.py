"""Tests for ariadne.utils.logging."""

import logging

from ariadne.utils.logging import get_logger


def test_get_logger_returns_named_logger_under_ariadne_namespace():
    logger = get_logger("ariadne.propagate.sgp4")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "ariadne.propagate.sgp4"


def test_get_logger_configures_root_level_from_settings():
    get_logger(__name__)
    root = logging.getLogger("ariadne")
    assert logging.getLevelName(root.level) in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
    assert root.handlers, "expected _configure_root to attach a handler"


def test_get_logger_does_not_duplicate_handlers_on_repeated_calls():
    get_logger("a")
    handler_count = len(logging.getLogger("ariadne").handlers)
    get_logger("b")
    assert len(logging.getLogger("ariadne").handlers) == handler_count
