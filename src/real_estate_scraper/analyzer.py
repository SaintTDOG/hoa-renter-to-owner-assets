"""Market analysis engine — turns raw listings into actionable insights."""

from __future__ import annotations

import statistics
from typing import Optional

from .models import Listing, MarketSnapshot


def build_market_snapshot(listings: list[Listing]) -> Optional[MarketSnapshot]:
    """Aggregate a list of listings into a MarketSnapshot.

    Returns None when there are fewer than 2 listings to compare.
    """
    priced = [l for l in listings if l.price > 0]
    if len(priced) < 2:
        return None

    prices = [l.price for l in priced]
    sqms = [l.sqm for l in priced if l.sqm > 0]
    ppsqms = [l.price_per_sqm for l in priced if l.price_per_sqm and l.price_per_sqm > 0]
    doms = [l.days_on_market for l in priced if l.days_on_market is not None]

    return MarketSnapshot(
        median_price=int(statistics.median(prices)),
        median_price_per_sqm=round(statistics.median(ppsqms), 2) if ppsqms else 0.0,
        avg_days_on_market=round(statistics.mean(doms), 1) if doms else 0.0,
        total_active_listings=len(priced),
        price_range=(min(prices), max(prices)),
        median_sqm=int(statistics.median(sqms)) if sqms else 0,
    )


def price_position(listing: Listing, snapshot: MarketSnapshot) -> str:
    """Describe how a listing's price compares to the market median."""
    if snapshot.median_price == 0:
        return "insufficient data"
    pct = ((listing.price - snapshot.median_price) / snapshot.median_price) * 100
    if pct < -10:
        return f"{abs(pct):.0f}% below median — potential bargain"
    if pct < 0:
        return f"{abs(pct):.0f}% below median — slightly under market"
    if pct < 10:
        return f"{pct:.0f}% above median — near market value"
    return f"{pct:.0f}% above median — premium priced"


def sqm_value_position(listing: Listing, snapshot: MarketSnapshot) -> str:
    """Describe $/sqm relative to the market."""
    if not listing.price_per_sqm or snapshot.median_price_per_sqm == 0:
        return "insufficient data"
    pct = ((listing.price_per_sqm - snapshot.median_price_per_sqm)
           / snapshot.median_price_per_sqm) * 100
    if pct < -10:
        return f"${listing.price_per_sqm:,.0f}/m² — {abs(pct):.0f}% below area median (good value)"
    if pct < 5:
        return f"${listing.price_per_sqm:,.0f}/m² — near area median"
    return f"${listing.price_per_sqm:,.0f}/m² — {pct:.0f}% above area median (premium)"
