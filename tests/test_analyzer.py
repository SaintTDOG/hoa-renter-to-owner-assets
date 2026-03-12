"""Tests for the market analysis engine."""

from real_estate_scraper.analyzer import (
    build_market_snapshot,
    price_position,
    sqm_value_position,
)
from real_estate_scraper.models import Listing, MarketSnapshot


def _make_listing(price: int, sqm: int = 120, dom: int | None = None) -> Listing:
    return Listing(
        address="Test, Melbourne VIC",
        price=price,
        bedrooms=3,
        bathrooms=2,
        sqm=sqm,
        days_on_market=dom,
    )


def test_build_market_snapshot_basic():
    listings = [_make_listing(800_000), _make_listing(1_000_000), _make_listing(900_000)]
    snap = build_market_snapshot(listings)
    assert snap is not None
    assert snap.median_price == 900_000
    assert snap.total_active_listings == 3
    assert snap.price_range == (800_000, 1_000_000)


def test_build_market_snapshot_too_few():
    assert build_market_snapshot([_make_listing(500_000)]) is None
    assert build_market_snapshot([]) is None


def test_price_position_below():
    snap = MarketSnapshot(
        median_price=900_000,
        median_price_per_sqm=7_500.0,
        avg_days_on_market=30.0,
        total_active_listings=10,
        price_range=(700_000, 1_100_000),
        median_sqm=120,
    )
    result = price_position(_make_listing(750_000), snap)
    assert "below median" in result


def test_price_position_above():
    snap = MarketSnapshot(
        median_price=800_000,
        median_price_per_sqm=6_667.0,
        avg_days_on_market=30.0,
        total_active_listings=10,
        price_range=(600_000, 1_000_000),
        median_sqm=120,
    )
    result = price_position(_make_listing(950_000), snap)
    assert "above median" in result


def test_sqm_value_position_good_value():
    snap = MarketSnapshot(
        median_price=900_000,
        median_price_per_sqm=10_000.0,
        avg_days_on_market=30.0,
        total_active_listings=10,
        price_range=(700_000, 1_100_000),
        median_sqm=90,
    )
    # $800k / 120m² = $6,667/m² vs $10,000 median → good value
    result = sqm_value_position(_make_listing(800_000, sqm=120), snap)
    assert "below" in result or "good value" in result
