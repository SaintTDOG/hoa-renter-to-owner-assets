"""FastAPI service exposing a 'Should I Buy?' endpoint for PropertyIQ."""

from __future__ import annotations

import os
import time
from dataclasses import asdict
from threading import Lock
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .advisor import advise_on_listing, format_advice
from .analyzer import build_market_snapshot
from .models import Listing, ListingStatus, PropertyType
from .scraper import (
    DomainScraper,
    GumtreeScraper,
    RealestateComAuScraper,
    get_all_scrapers,
)

_SCRAPER_MAP = {
    "domain": DomainScraper,
    "rea": RealestateComAuScraper,
    "gumtree": GumtreeScraper,
}

_ALLOWED_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "https://your-propertyiq.pages.dev,http://localhost:3000",
).split(",")

_CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", "900"))  # 15 min default

app = FastAPI(
    title="PropertyIQ — Should I Buy?",
    description="Australian real estate scraper and purchase advisor API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# --- Simple TTL cache ---

_cache: dict[str, tuple[float, list[Listing]]] = {}
_cache_lock = Lock()


def _get_cached(key: str) -> list[Listing] | None:
    with _cache_lock:
        entry = _cache.get(key)
        if entry and (time.monotonic() - entry[0]) < _CACHE_TTL:
            return entry[1]
        _cache.pop(key, None)
        return None


def _set_cached(key: str, listings: list[Listing]) -> None:
    with _cache_lock:
        _cache[key] = (time.monotonic(), listings)


# --- Response models ---

class ListingResponse(BaseModel):
    address: str
    price: int
    bedrooms: int
    bathrooms: float
    sqm: int
    parking: Optional[int] = None
    property_type: str
    status: str
    url: str
    price_per_sqm: Optional[float] = None
    strata_levy: Optional[int] = None
    days_on_market: Optional[int] = None


class MarketSummaryResponse(BaseModel):
    median_price: int
    median_price_per_sqm: float
    avg_days_on_market: float
    total_active_listings: int
    price_range_low: int
    price_range_high: int
    median_sqm: int


class OfferAdviceResponse(BaseModel):
    suggested_offer_low: int
    suggested_offer_high: int
    price_assessment: str
    value_assessment: str
    tips: list[str]


class ShouldIBuyResponse(BaseModel):
    location: str
    listing: ListingResponse
    market_summary: Optional[MarketSummaryResponse] = None
    advice: OfferAdviceResponse
    verdict: str
    report: str


class SearchResponse(BaseModel):
    location: str
    source: str
    total: int
    listings: list[ListingResponse]
    market_summary: Optional[MarketSummaryResponse] = None


# --- Helpers ---

def _listing_to_response(listing: Listing) -> ListingResponse:
    return ListingResponse(
        address=listing.address,
        price=listing.price,
        bedrooms=listing.bedrooms,
        bathrooms=listing.bathrooms,
        sqm=listing.sqm,
        parking=listing.parking,
        property_type=listing.property_type.value,
        status=listing.status.value,
        url=listing.url,
        price_per_sqm=listing.price_per_sqm,
        strata_levy=listing.strata_levy,
        days_on_market=listing.days_on_market,
    )


def _market_summary(listings: list[Listing]) -> Optional[MarketSummaryResponse]:
    snap = build_market_snapshot(listings)
    if not snap:
        return None
    return MarketSummaryResponse(
        median_price=snap.median_price,
        median_price_per_sqm=snap.median_price_per_sqm,
        avg_days_on_market=snap.avg_days_on_market,
        total_active_listings=snap.total_active_listings,
        price_range_low=snap.price_range[0],
        price_range_high=snap.price_range[1],
        median_sqm=snap.median_sqm,
    )


def _filter_comparables(target: Listing, all_listings: list[Listing]) -> list[Listing]:
    """Filter comparables to the same property type and similar bedroom count."""
    same_type = [
        l for l in all_listings
        if l is not target and l.property_type == target.property_type
    ]
    if len(same_type) >= 2:
        return same_type

    return [l for l in all_listings if l is not target]


def _verdict(advice) -> str:
    """Generate a plain-English verdict from the offer advice."""
    listing = advice.listing
    price_a = advice.price_assessment.lower()
    value_a = advice.value_assessment.lower()

    if "no comparables" in price_a or "insufficient" in price_a:
        return "Not enough market data to assess — do your own research on this area."

    if "bargain" in price_a or "good value" in value_a:
        return "Looks like a good buy — priced below the local market."
    if "below market" in price_a or "below market" in value_a:
        return "Slightly under market — could be a good opportunity if it checks out."
    if "premium" in price_a and "premium" in value_a:
        return "Expensive for the area — negotiate hard or consider alternatives."
    if "premium" in price_a:
        return "Above-market price, but the per-m² rate is reasonable. Negotiate."
    if "premium" in value_a:
        return "High cost per m² for the area — check what justifies the premium."
    if listing.status == ListingStatus.AUCTION:
        return "Going to auction — do your homework before bidding."
    if listing.days_on_market and listing.days_on_market > 90:
        return "Been on the market a while — the vendor may be flexible on price."
    return "Fairly priced for the area — a competitive offer could secure it."


def _scrape_listings(location: str, source: str, max_results: int) -> list[Listing]:
    """Scrape listings with caching."""
    cache_key = f"{location.lower().strip()}|{source}|{max_results}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    delay = float(os.getenv("SCRAPER_DELAY", "1.0"))
    kwargs = {"delay": delay}

    if source == "all":
        scrapers = get_all_scrapers(**kwargs)
    elif source in _SCRAPER_MAP:
        scrapers = [_SCRAPER_MAP[source](**kwargs)]
    else:
        raise HTTPException(400, f"Unknown source '{source}'. Use: domain, rea, gumtree, all")

    all_listings: list[Listing] = []
    for scraper in scrapers:
        all_listings.extend(scraper.search(location, max_results=max_results))

    _set_cached(cache_key, all_listings)
    return all_listings


# --- Routes ---

@app.get("/healthz")
async def health():
    return {"status": "ok"}


@app.get("/api/search", response_model=SearchResponse)
async def search_listings(
    location: str = Query(..., description="e.g. 'Melbourne, VIC'"),
    source: str = Query("all", description="domain | rea | gumtree | all"),
    max_results: int = Query(20, ge=1, le=50),
):
    """Search Australian real estate listings by location."""
    all_listings = _scrape_listings(location, source, max_results)

    return SearchResponse(
        location=location,
        source=source,
        total=len(all_listings),
        listings=[_listing_to_response(l) for l in all_listings],
        market_summary=_market_summary(all_listings),
    )


@app.get("/api/should-i-buy", response_model=ShouldIBuyResponse)
async def should_i_buy(
    location: str = Query(..., description="e.g. 'Melbourne, VIC'"),
    index: int = Query(0, ge=0, description="0-based index of the listing to analyse"),
    source: str = Query("all", description="domain | rea | gumtree | all"),
    max_results: int = Query(20, ge=1, le=50),
):
    """Scrape listings, then return 'Should I Buy?' advice for a specific one."""
    all_listings = _scrape_listings(location, source, max_results)

    if not all_listings:
        raise HTTPException(404, f"No listings found for '{location}'.")
    if index >= len(all_listings):
        raise HTTPException(
            400,
            f"Index {index} out of range — only {len(all_listings)} listings found.",
        )

    target = all_listings[index]
    comparables = _filter_comparables(target, all_listings)
    advice = advise_on_listing(target, comparables)
    report = format_advice(advice)

    return ShouldIBuyResponse(
        location=location,
        listing=_listing_to_response(target),
        market_summary=_market_summary(all_listings),
        advice=OfferAdviceResponse(
            suggested_offer_low=advice.suggested_offer_low,
            suggested_offer_high=advice.suggested_offer_high,
            price_assessment=advice.price_assessment,
            value_assessment=advice.value_assessment,
            tips=advice.tips,
        ),
        verdict=_verdict(advice),
        report=report,
    )
