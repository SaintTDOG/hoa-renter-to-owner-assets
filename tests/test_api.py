"""Tests for the FastAPI 'Should I Buy?' endpoints (no network calls)."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from real_estate_scraper.api import app
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


@pytest.fixture
def client():
    return TestClient(app)


def test_health(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@patch("real_estate_scraper.api.get_all_scrapers")
def test_search_returns_listings(mock_scrapers, client):
    mock_scraper = type("MockScraper", (), {
        "search": lambda self, loc, max_results=20: _fake_listings(),
        "name": lambda self: "Mock",
    })()
    mock_scrapers.return_value = [mock_scraper]

    resp = client.get("/api/search?location=Melbourne,+VIC")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert len(data["listings"]) == 3
    assert data["listings"][0]["price"] == 900_000


@patch("real_estate_scraper.api.get_all_scrapers")
def test_should_i_buy_returns_advice(mock_scrapers, client):
    mock_scraper = type("MockScraper", (), {
        "search": lambda self, loc, max_results=20: _fake_listings(),
        "name": lambda self: "Mock",
    })()
    mock_scrapers.return_value = [mock_scraper]

    resp = client.get("/api/should-i-buy?location=Melbourne,+VIC&index=0")
    assert resp.status_code == 200
    data = resp.json()
    assert "verdict" in data
    assert data["listing"]["address"] == "1 Collins St, Melbourne VIC"
    assert data["advice"]["suggested_offer_low"] < 900_000
    assert len(data["advice"]["tips"]) > 0


@patch("real_estate_scraper.api.get_all_scrapers")
def test_should_i_buy_index_out_of_range(mock_scrapers, client):
    mock_scraper = type("MockScraper", (), {
        "search": lambda self, loc, max_results=20: _fake_listings(),
        "name": lambda self: "Mock",
    })()
    mock_scrapers.return_value = [mock_scraper]

    resp = client.get("/api/should-i-buy?location=Melbourne,+VIC&index=99")
    assert resp.status_code == 400


@patch("real_estate_scraper.api.get_all_scrapers")
def test_should_i_buy_no_listings(mock_scrapers, client):
    mock_scraper = type("MockScraper", (), {
        "search": lambda self, loc, max_results=20: [],
        "name": lambda self: "Mock",
    })()
    mock_scrapers.return_value = [mock_scraper]

    resp = client.get("/api/should-i-buy?location=Nowhere")
    assert resp.status_code == 404


def test_search_missing_location(client):
    resp = client.get("/api/search")
    assert resp.status_code == 422  # FastAPI validation error


def test_search_invalid_source(client):
    resp = client.get("/api/search?location=Melbourne&source=zillow")
    assert resp.status_code == 400
