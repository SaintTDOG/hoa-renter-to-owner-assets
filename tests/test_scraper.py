"""Tests for scraper utilities (no network calls)."""

from real_estate_scraper.scraper import (
    _safe_int,
    _safe_float,
    _parse_price,
    _guess_property_type,
    get_all_scrapers,
)
from real_estate_scraper.models import PropertyType


# --- _safe_int (used for non-price fields like beds/sqm) ---

def test_safe_int_with_dollar_commas():
    assert _safe_int("$850,000") == 850000


def test_safe_int_empty():
    assert _safe_int("") == 0
    assert _safe_int(None) == 0


def test_safe_int_default():
    assert _safe_int("abc", default=42) == 42


# --- _parse_price (used for listing prices) ---

def test_parse_price_basic():
    assert _parse_price("$850,000") == 850_000


def test_parse_price_range_takes_first():
    assert _parse_price("$850,000 - $900,000") == 850_000


def test_parse_price_k_suffix():
    assert _parse_price("$850k") == 850_000


def test_parse_price_m_suffix():
    assert _parse_price("$1.2m") == 1_200_000


def test_parse_price_contact_agent():
    assert _parse_price("Contact Agent") == 0


def test_parse_price_eoi():
    assert _parse_price("Expressions of Interest") == 0


def test_parse_price_auction_with_date():
    assert _parse_price("Auction Sat 15 Mar") == 0


def test_parse_price_below_floor():
    assert _parse_price("$500") == 0


def test_parse_price_none():
    assert _parse_price(None) == 0


def test_parse_price_empty():
    assert _parse_price("") == 0


def test_parse_price_offers_over():
    assert _parse_price("Offers over $1.2m") == 1_200_000


# --- _safe_float ---

def test_safe_float_basic():
    assert _safe_float("2.5 baths") == 2.5


def test_safe_float_empty():
    assert _safe_float("") == 0.0
    assert _safe_float(None) == 0.0


# --- _guess_property_type ---

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


# --- get_all_scrapers ---

def test_get_all_scrapers_returns_three():
    scrapers = get_all_scrapers()
    assert len(scrapers) == 3
    names = {s.name() for s in scrapers}
    assert "Domain.com.au" in names
    assert "Realestate.com.au" in names
    assert "Gumtree.com.au" in names
