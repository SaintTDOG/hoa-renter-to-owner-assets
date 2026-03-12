"""Tests for the Australian negotiation advisor."""

from real_estate_scraper.advisor import advise_on_listing, format_advice
from real_estate_scraper.models import Listing, ListingStatus, PropertyType


def _make_listing(
    price: int,
    dom: int | None = 30,
    strata: int | None = None,
    status: ListingStatus = ListingStatus.ACTIVE,
    prop_type: PropertyType = PropertyType.HOUSE,
) -> Listing:
    return Listing(
        address="42 Bourke St, Melbourne VIC 3000",
        price=price,
        bedrooms=3,
        bathrooms=2,
        sqm=150,
        days_on_market=dom,
        strata_levy=strata,
        status=status,
        property_type=prop_type,
    )


def _comparables() -> list[Listing]:
    return [
        _make_listing(850_000, dom=20),
        _make_listing(950_000, dom=40),
        _make_listing(900_000, dom=25),
        _make_listing(1_000_000, dom=60),
    ]


def test_advise_returns_offer_range():
    target = _make_listing(920_000, dom=45)
    advice = advise_on_listing(target, _comparables())
    assert advice.suggested_offer_low < advice.listing.price
    assert advice.suggested_offer_high <= advice.listing.price


def test_advise_long_dom_lower_offer():
    stale = _make_listing(920_000, dom=120)
    fresh = _make_listing(920_000, dom=5)
    advice_stale = advise_on_listing(stale, _comparables())
    advice_fresh = advise_on_listing(fresh, _comparables())
    assert advice_stale.suggested_offer_low < advice_fresh.suggested_offer_low


def test_advise_includes_strata_tip():
    target = _make_listing(750_000, strata=1200, prop_type=PropertyType.APARTMENT)
    advice = advise_on_listing(target, _comparables())
    strata_tips = [t for t in advice.tips if "strata" in t.lower() or "sinking fund" in t.lower()]
    assert len(strata_tips) > 0


def test_advise_includes_stamp_duty_tip():
    target = _make_listing(900_000)
    advice = advise_on_listing(target, _comparables())
    stamp_tips = [t for t in advice.tips if "stamp duty" in t.lower() or "transfer duty" in t.lower()]
    assert len(stamp_tips) > 0


def test_advise_includes_building_pest_tip():
    target = _make_listing(900_000)
    advice = advise_on_listing(target, _comparables())
    inspection_tips = [t for t in advice.tips if "building" in t.lower() and "pest" in t.lower()]
    assert len(inspection_tips) > 0


def test_advise_auction_tips():
    target = _make_listing(900_000, status=ListingStatus.AUCTION)
    advice = advise_on_listing(target, _comparables())
    auction_tips = [t for t in advice.tips if "auction" in t.lower()]
    assert len(auction_tips) > 0


def test_advise_auction_higher_offer_range():
    auction = _make_listing(900_000, dom=30, status=ListingStatus.AUCTION)
    private = _make_listing(900_000, dom=30, status=ListingStatus.ACTIVE)
    advice_auction = advise_on_listing(auction, _comparables())
    advice_private = advise_on_listing(private, _comparables())
    assert advice_auction.suggested_offer_low >= advice_private.suggested_offer_low


def test_advise_includes_cooling_off_tip():
    target = _make_listing(900_000)
    advice = advise_on_listing(target, _comparables())
    cooling_tips = [t for t in advice.tips if "cooling-off" in t.lower() or "cooling off" in t.lower()]
    assert len(cooling_tips) > 0


def test_format_advice_readable():
    target = _make_listing(900_000, dom=30, strata=800, prop_type=PropertyType.APARTMENT)
    advice = advise_on_listing(target, _comparables())
    text = format_advice(advice)
    assert "PROPERTY" in text
    assert "GUIDE PRICE" in text
    assert "AUD" in text
    assert "SUGGESTED OFFER RANGE" in text
    assert "NEGOTIATION" in text


def test_advise_no_comparables():
    target = _make_listing(900_000)
    advice = advise_on_listing(target, [])
    assert "no comparables" in advice.price_assessment
    assert advice.suggested_offer_low > 0
