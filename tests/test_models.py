"""Tests for Australian data models."""

from real_estate_scraper.models import (
    Listing,
    ListingStatus,
    MarketSnapshot,
    PropertyType,
)


def test_listing_price_per_sqm_auto_calculated():
    l = Listing(address="10 Collins St, Melbourne VIC", price=900_000,
                bedrooms=2, bathrooms=1, sqm=75)
    assert l.price_per_sqm == 12_000.0


def test_listing_price_per_sqm_zero_sqm():
    l = Listing(address="10 Collins St", price=900_000,
                bedrooms=2, bathrooms=1, sqm=0)
    assert l.price_per_sqm is None


def test_listing_status_default():
    l = Listing(address="A", price=1, bedrooms=1, bathrooms=1, sqm=1)
    assert l.status == ListingStatus.ACTIVE


def test_listing_auction_status():
    l = Listing(address="A", price=1, bedrooms=1, bathrooms=1, sqm=1,
                status=ListingStatus.AUCTION)
    assert l.status == ListingStatus.AUCTION


def test_property_type_default():
    l = Listing(address="A", price=1, bedrooms=1, bathrooms=1, sqm=1)
    assert l.property_type == PropertyType.HOUSE


def test_market_snapshot_fields():
    snap = MarketSnapshot(
        median_price=850_000,
        median_price_per_sqm=10_000.0,
        avg_days_on_market=30.0,
        total_active_listings=10,
        price_range=(600_000, 1_200_000),
        median_sqm=85,
    )
    assert snap.price_range[0] == 600_000
    assert snap.median_sqm == 85
