"""Tests for ariadne.fetch.cache."""

import os
import time

import pytest

from ariadne.exceptions import FetchError
from ariadne.fetch import cache


@pytest.fixture(autouse=True)
def _cache_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "CACHE_DIR", tmp_path)
    return tmp_path


def test_fetches_fresh_on_first_call():
    calls = []

    def fetch_fn():
        calls.append(1)
        return "payload-v1"

    result = cache.get_cached("celestrak", "GROUP=active", fetch_fn)

    assert result.text == "payload-v1"
    assert result.is_stale is False
    assert result.age_hours == 0.0
    assert len(calls) == 1


def test_returns_cached_payload_within_ttl_without_refetching():
    calls = []

    def fetch_fn():
        calls.append(1)
        return f"payload-v{len(calls)}"

    first = cache.get_cached("celestrak", "GROUP=active", fetch_fn, ttl_hours=6.0)
    second = cache.get_cached("celestrak", "GROUP=active", fetch_fn, ttl_hours=6.0)

    assert first.text == second.text == "payload-v1"
    assert second.is_stale is False
    assert len(calls) == 1


def test_refetches_once_ttl_expires(_cache_dir):
    calls = []

    def fetch_fn():
        calls.append(1)
        return f"payload-v{len(calls)}"

    cache.get_cached("celestrak", "GROUP=active", fetch_fn, ttl_hours=6.0)

    path = cache._cache_path("celestrak", "GROUP=active")
    old_time = time.time() - 7 * 3600
    os.utime(path, (old_time, old_time))

    result = cache.get_cached("celestrak", "GROUP=active", fetch_fn, ttl_hours=6.0)

    assert result.text == "payload-v2"
    assert result.is_stale is False
    assert len(calls) == 2


def test_falls_back_to_stale_cache_on_fetch_failure(_cache_dir):
    cache.get_cached("celestrak", "GROUP=active", lambda: "payload-v1")

    path = cache._cache_path("celestrak", "GROUP=active")
    old_time = time.time() - 7 * 3600
    os.utime(path, (old_time, old_time))

    def failing_fetch():
        raise FetchError("network down")

    result = cache.get_cached("celestrak", "GROUP=active", failing_fetch, ttl_hours=6.0)

    assert result.text == "payload-v1"
    assert result.is_stale is True
    assert result.age_hours > 6.0


def test_raises_fetch_error_when_no_cache_and_fetch_fails():
    def failing_fetch():
        raise FetchError("network down")

    with pytest.raises(FetchError):
        cache.get_cached("celestrak", "GROUP=active", failing_fetch)


def test_different_queries_are_cached_separately():
    cache.get_cached("celestrak", "GROUP=active", lambda: "active-payload")
    cache.get_cached("celestrak", "GROUP=stations", lambda: "stations-payload")

    active = cache.get_cached("celestrak", "GROUP=active", lambda: "should-not-be-called")
    stations = cache.get_cached("celestrak", "GROUP=stations", lambda: "should-not-be-called")

    assert active.text == "active-payload"
    assert stations.text == "stations-payload"
