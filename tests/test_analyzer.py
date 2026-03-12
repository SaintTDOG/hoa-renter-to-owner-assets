"""Tests for the market analysis engine."""

from real_estate_scraper.analyzer import (
    build_market_snapshot,
    price_position,
    sqft_value_position,
)
from real_estate_scraper.models import Listing, MarketSnapshot


def _make_listing(price: int, sqft: int = 1500, dom: int | None = None) -> Listing:
    return Listing(
        address="Test",
        price=price,
        bedrooms=3,
        bathrooms=2,
        sqft=sqft,
        days_on_market=dom,
    )


def test_build_market_snapshot_basic():
    listings = [_make_listing(300_000), _make_listing(400_000), _make_listing(350_000)]
    snap = build_market_snapshot(listings)
    assert snap is not None
    assert snap.median_price == 350_000
    assert snap.total_active_listings == 3
    assert snap.price_range == (300_000, 400_000)


def test_build_market_snapshot_too_few():
    assert build_market_snapshot([_make_listing(100_000)]) is None
    assert build_market_snapshot([]) is None


def test_price_position_below():
    snap = MarketSnapshot(
        median_price=400_000,
        median_price_per_sqft=250.0,
        avg_days_on_market=30.0,
        total_active_listings=10,
        price_range=(300_000, 500_000),
        median_sqft=1600,
    )
    result = price_position(_make_listing(340_000), snap)
    assert "below median" in result


def test_price_position_above():
    snap = MarketSnapshot(
        median_price=300_000,
        median_price_per_sqft=200.0,
        avg_days_on_market=30.0,
        total_active_listings=10,
        price_range=(200_000, 400_000),
        median_sqft=1500,
    )
    result = price_position(_make_listing(360_000), snap)
    assert "above median" in result


def test_sqft_value_position_good_value():
    snap = MarketSnapshot(
        median_price=400_000,
        median_price_per_sqft=300.0,
        avg_days_on_market=30.0,
        total_active_listings=10,
        price_range=(300_000, 500_000),
        median_sqft=1333,
    )
    # 200 $/sqft vs 300 median → good value
    result = sqft_value_position(_make_listing(300_000, sqft=1500), snap)
    assert "below" in result or "good value" in result
