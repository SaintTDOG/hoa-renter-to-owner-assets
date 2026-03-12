"""Tests for scraper utilities (no network calls)."""

from real_estate_scraper.scraper import (
    _safe_int,
    _safe_float,
    _guess_property_type,
    get_all_scrapers,
)
from real_estate_scraper.models import PropertyType


def test_safe_int_with_dollar_commas():
    assert _safe_int("$850,000") == 850000


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


def test_guess_property_type_apartment():
    assert _guess_property_type("2 bed apartment in Surry Hills") == PropertyType.APARTMENT
    assert _guess_property_type("Modern unit in CBD") == PropertyType.APARTMENT


def test_guess_property_type_townhouse():
    assert _guess_property_type("3 bed townhouse") == PropertyType.TOWNHOUSE
    assert _guess_property_type("Terrace in Paddington") == PropertyType.TOWNHOUSE


def test_guess_property_type_house():
    assert _guess_property_type("Family home in Kew") == PropertyType.HOUSE


def test_guess_property_type_land():
    assert _guess_property_type("Vacant land 600m²") == PropertyType.LAND


def test_guess_property_type_rural():
    assert _guess_property_type("50 acre farm") == PropertyType.RURAL
    assert _guess_property_type("Acreage property") == PropertyType.RURAL


def test_get_all_scrapers_returns_three():
    scrapers = get_all_scrapers()
    assert len(scrapers) == 3
    names = {s.name() for s in scrapers}
    assert "Domain.com.au" in names
    assert "Realestate.com.au" in names
    assert "Gumtree.com.au" in names
