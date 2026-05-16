"""Tests for the FastAPI 'Should I Buy?' endpoints (no network calls)."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from real_estate_scraper.api import app, _verdict
from real_estate_scraper.models import Listing, ListingStatus, PropertyType


def _fake_listings():
    return [
        Listing(address="1 Collins St, Melbourne VIC", price=900_000,
                bedrooms=3, bathrooms=2, sqm=120, days_on_market=30),
        Listing(address="2 Bourke St, Melbourne VIC", price=850_000,
                bedrooms=2, bathrooms=1, sqm=95, days_on_market=45),
        Listing(address="3 Flinders St, Melbourne VIC", price=1_100_000,
                bedrooms=4, bathrooms=2, sqm=180, days_on_market=10),
    ]


def _mixed_type_listings():
    return [
        Listing(address="1 Collins St", price=900_000, bedrooms=3,
                bathrooms=2, sqm=120, property_type=PropertyType.HOUSE),
        Listing(address="2 Bourke St", price=500_000, bedrooms=2,
                bathrooms=1, sqm=60, property_type=PropertyType.APARTMENT),
        Listing(address="3 Lonsdale St", price=950_000, bedrooms=3,
                bathrooms=2, sqm=130, property_type=PropertyType.HOUSE),
        Listing(address="4 Spring St", price=480_000, bedrooms=1,
                bathrooms=1, sqm=50, property_type=PropertyType.APARTMENT),
    ]


@pytest.fixture
def client():
    return TestClient(app)


def test_health(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@patch("real_estate_scraper.api._scrape_listings")
def test_search_returns_listings(mock_scrape, client):
    mock_scrape.return_value = _fake_listings()
    resp = client.get("/api/search?location=Melbourne,+VIC")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert len(data["listings"]) == 3
    assert data["listings"][0]["price"] == 900_000


@patch("real_estate_scraper.api._scrape_listings")
def test_should_i_buy_returns_advice(mock_scrape, client):
    mock_scrape.return_value = _fake_listings()
    resp = client.get("/api/should-i-buy?location=Melbourne,+VIC&index=0")
    assert resp.status_code == 200
    data = resp.json()
    assert "verdict" in data
    assert data["listing"]["address"] == "1 Collins St, Melbourne VIC"
    assert data["advice"]["suggested_offer_low"] < 900_000
    assert len(data["advice"]["tips"]) > 0


@patch("real_estate_scraper.api._scrape_listings")
def test_should_i_buy_index_out_of_range(mock_scrape, client):
    mock_scrape.return_value = _fake_listings()
    resp = client.get("/api/should-i-buy?location=Melbourne,+VIC&index=99")
    assert resp.status_code == 400


@patch("real_estate_scraper.api._scrape_listings")
def test_should_i_buy_no_listings(mock_scrape, client):
    mock_scrape.return_value = []
    resp = client.get("/api/should-i-buy?location=Nowhere")
    assert resp.status_code == 404


def test_search_missing_location(client):
    resp = client.get("/api/search")
    assert resp.status_code == 422


def test_verdict_no_comparables():
    class FakeAdvice:
        listing = Listing(address="X", price=1, bedrooms=1, bathrooms=1, sqm=1)
        price_assessment = "no comparables available"
        value_assessment = "no comparables available"
    v = _verdict(FakeAdvice())
    assert "not enough" in v.lower() or "research" in v.lower()


def test_verdict_below_market():
    class FakeAdvice:
        listing = Listing(address="X", price=1, bedrooms=1, bathrooms=1, sqm=1)
        price_assessment = "5% below median — slightly under market"
        value_assessment = "$7,000/m² — 5% below area median (below market)"
    v = _verdict(FakeAdvice())
    assert "under market" in v.lower() or "opportunity" in v.lower()


def test_verdict_premium_value_only():
    class FakeAdvice:
        listing = Listing(address="X", price=1, bedrooms=1, bathrooms=1, sqm=1)
        price_assessment = "right at market value"
        value_assessment = "$12,000/m² — 15% above area median (premium)"
    v = _verdict(FakeAdvice())
    assert "premium" in v.lower() or "per m²" in v.lower() or "per-m²" in v.lower()
