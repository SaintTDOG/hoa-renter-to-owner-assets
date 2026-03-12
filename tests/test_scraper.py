"""Tests for scraper utilities (no network calls)."""

from real_estate_scraper.scraper import _safe_int, _safe_float, get_all_scrapers


def test_safe_int_with_dollar_commas():
    assert _safe_int("$350,000") == 350000


def test_safe_int_empty():
    assert _safe_int("") == 0
    assert _safe_int(None) == 0


def test_safe_int_default():
    assert _safe_int("abc", default=42) == 42


def test_safe_float_basic():
    assert _safe_float("2.5 baths") == 2.5


def test_safe_float_empty():
    assert _safe_float("") == 0.0
    assert _safe_float(None) == 0.0


def test_get_all_scrapers_returns_three():
    scrapers = get_all_scrapers()
    assert len(scrapers) == 3
    names = {s.name() for s in scrapers}
    assert "Realtor.com" in names
    assert "Redfin" in names
    assert "Craigslist" in names
