"""Tests for data models."""

from real_estate_scraper.models import Listing, ListingStatus, MarketSnapshot


def test_listing_price_per_sqft_auto_calculated():
    l = Listing(address="123 Main St", price=300_000, bedrooms=3, bathrooms=2, sqft=1500)
    assert l.price_per_sqft == 200.0


def test_listing_price_per_sqft_zero_sqft():
    l = Listing(address="123 Main St", price=300_000, bedrooms=3, bathrooms=2, sqft=0)
    assert l.price_per_sqft is None


def test_listing_status_default():
    l = Listing(address="A", price=1, bedrooms=1, bathrooms=1, sqft=1)
    assert l.status == ListingStatus.ACTIVE


def test_market_snapshot_fields():
    snap = MarketSnapshot(
        median_price=350_000,
        median_price_per_sqft=200.0,
        avg_days_on_market=30.0,
        total_active_listings=10,
        price_range=(200_000, 500_000),
        median_sqft=1750,
    )
    assert snap.price_range[0] == 200_000
    assert snap.median_sqft == 1750
