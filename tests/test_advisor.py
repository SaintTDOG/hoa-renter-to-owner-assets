"""Tests for the negotiation advisor."""

from real_estate_scraper.advisor import advise_on_listing, format_advice
from real_estate_scraper.models import Listing


def _make_listing(price: int, dom: int | None = 30, hoa: int | None = None) -> Listing:
    return Listing(
        address="456 Oak Ave, Austin TX",
        price=price,
        bedrooms=3,
        bathrooms=2,
        sqft=1800,
        days_on_market=dom,
        hoa_fee=hoa,
    )


def _comparables() -> list[Listing]:
    return [
        _make_listing(350_000, dom=20),
        _make_listing(400_000, dom=40),
        _make_listing(380_000, dom=25),
        _make_listing(420_000, dom=60),
    ]


def test_advise_returns_offer_range():
    target = _make_listing(390_000, dom=45)
    advice = advise_on_listing(target, _comparables())
    assert advice.suggested_offer_low < advice.listing.price
    assert advice.suggested_offer_high <= advice.listing.price


def test_advise_long_dom_lower_offer():
    stale = _make_listing(390_000, dom=120)
    fresh = _make_listing(390_000, dom=5)
    advice_stale = advise_on_listing(stale, _comparables())
    advice_fresh = advise_on_listing(fresh, _comparables())
    assert advice_stale.suggested_offer_low < advice_fresh.suggested_offer_low


def test_advise_includes_hoa_tip():
    target = _make_listing(390_000, hoa=500)
    advice = advise_on_listing(target, _comparables())
    hoa_tips = [t for t in advice.tips if "HOA" in t or "hoa" in t.lower()]
    assert len(hoa_tips) > 0


def test_advise_includes_inspection_tip():
    target = _make_listing(390_000)
    advice = advise_on_listing(target, _comparables())
    inspection_tips = [t for t in advice.tips if "inspection" in t.lower()]
    assert len(inspection_tips) > 0


def test_format_advice_readable():
    target = _make_listing(390_000, dom=30, hoa=200)
    advice = advise_on_listing(target, _comparables())
    text = format_advice(advice)
    assert "PROPERTY" in text
    assert "ASKING PRICE" in text
    assert "SUGGESTED OFFER RANGE" in text
    assert "NEGOTIATION" in text


def test_advise_no_comparables():
    target = _make_listing(390_000)
    advice = advise_on_listing(target, [])
    assert "no comparables" in advice.price_assessment
    assert advice.suggested_offer_low > 0
