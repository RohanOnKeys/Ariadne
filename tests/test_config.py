"""Tests for ariadne.config.settings."""

import importlib
from pathlib import Path

from ariadne.config import settings


def _reload_with_env(monkeypatch, **env):
    for key in ("CACHE_DIR", "LOG_LEVEL", "SPACETRACK_USERNAME", "SPACETRACK_PASSWORD"):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    return importlib.reload(settings)


def test_defaults_when_env_unset(monkeypatch):
    reloaded = _reload_with_env(monkeypatch)
    assert reloaded.CACHE_DIR == Path("./data/catalogs")
    assert reloaded.LOG_LEVEL == "INFO"
    assert reloaded.SPACETRACK_USERNAME is None
    assert reloaded.SPACETRACK_PASSWORD is None


def test_env_overrides_are_picked_up(monkeypatch):
    reloaded = _reload_with_env(
        monkeypatch,
        CACHE_DIR="/tmp/cache",
        LOG_LEVEL="debug",
        SPACETRACK_USERNAME="alice",
        SPACETRACK_PASSWORD="hunter2",
    )
    assert reloaded.CACHE_DIR == Path("/tmp/cache")
    assert reloaded.LOG_LEVEL == "DEBUG"
    assert reloaded.SPACETRACK_USERNAME == "alice"
    assert reloaded.SPACETRACK_PASSWORD == "hunter2"


def teardown_module(module):
    """Leave the module in its default (env-unset) state for anything
    imported after this test module runs."""
    importlib.reload(settings)
