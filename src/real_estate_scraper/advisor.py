"""Negotiation and purchase advisor — generates advice from market data."""

from __future__ import annotations

from dataclasses import dataclass, field

from .analyzer import build_market_snapshot, price_position, sqft_value_position
from .models import Listing, MarketSnapshot


@dataclass
class OfferAdvice:
    """Structured negotiation advice for a single listing."""

    listing: Listing
    suggested_offer_low: int
    suggested_offer_high: int
    price_assessment: str
    value_assessment: str
    tips: list[str] = field(default_factory=list)


def _dom_tips(listing: Listing) -> list[str]:
    """Generate tips based on days-on-market."""
    dom = listing.days_on_market
    if dom is None:
        return ["Ask the listing agent how long the property has been on the market."]
    if dom > 90:
        return [
            f"This listing has been on the market for {dom} days — the seller may be motivated.",
            "Consider offering 8–12% below asking and negotiate from there.",
            "Ask the agent if there have been previous price reductions.",
        ]
    if dom > 45:
        return [
            f"On the market for {dom} days — moderate time, some negotiation room likely.",
            "Consider starting 5–8% below asking.",
        ]
    if dom > 14:
        return [
            f"Listed for {dom} days — still relatively fresh.",
            "A competitive offer 2–5% below asking is reasonable.",
        ]
    return [
        f"Only {dom} days on market — this is a fresh listing.",
        "In a competitive market, consider offering at or near asking price.",
        "If you really want this property, a strong initial offer reduces risk of losing it.",
    ]


def _hoa_tips(listing: Listing) -> list[str]:
    if listing.hoa_fee is None:
        return ["Confirm whether there is an HOA and its monthly fee before making an offer."]
    if listing.hoa_fee > 400:
        return [
            f"HOA fee is ${listing.hoa_fee}/mo — factor this into your monthly budget.",
            "Request the HOA's reserve study and meeting minutes to check for upcoming special assessments.",
        ]
    if listing.hoa_fee > 0:
        return [f"HOA fee is ${listing.hoa_fee}/mo — request a copy of CC&Rs before closing."]
    return []


def _general_purchase_tips() -> list[str]:
    return [
        "Always get a professional home inspection before finalizing your offer.",
        "Request seller disclosures early — look for past water damage, foundation issues, or unpermitted work.",
        "Get pre-approved (not just pre-qualified) for your mortgage to strengthen your offer.",
        "Include an appraisal contingency to protect against overpaying.",
        "Research the neighborhood: check school ratings, crime stats, and planned developments.",
        "Factor in closing costs (typically 2–5% of purchase price) when budgeting.",
    ]


def _offer_range(listing: Listing, snapshot: MarketSnapshot | None) -> tuple[int, int]:
    """Calculate suggested offer range based on market position."""
    if snapshot and snapshot.median_price > 0:
        pct_diff = (listing.price - snapshot.median_price) / snapshot.median_price

        if pct_diff > 0.15:
            # Overpriced relative to market
            low_pct, high_pct = 0.85, 0.93
        elif pct_diff > 0.05:
            low_pct, high_pct = 0.90, 0.97
        elif pct_diff < -0.10:
            # Already below market — less room to negotiate
            low_pct, high_pct = 0.95, 1.0
        else:
            low_pct, high_pct = 0.92, 0.98
    else:
        low_pct, high_pct = 0.90, 0.97

    # Adjust for days on market
    dom = listing.days_on_market
    if dom is not None and dom > 60:
        low_pct -= 0.03
        high_pct -= 0.02

    low = int(listing.price * low_pct)
    high = int(listing.price * high_pct)
    return low, high


def advise_on_listing(listing: Listing, comparables: list[Listing]) -> OfferAdvice:
    """Generate comprehensive negotiation advice for a listing."""
    snapshot = build_market_snapshot(comparables)
    price_assess = price_position(listing, snapshot) if snapshot else "no comparables available"
    value_assess = sqft_value_position(listing, snapshot) if snapshot else "no comparables available"
    offer_low, offer_high = _offer_range(listing, snapshot)

    tips: list[str] = []
    tips.extend(_dom_tips(listing))
    tips.extend(_hoa_tips(listing))
    tips.extend(_general_purchase_tips())

    return OfferAdvice(
        listing=listing,
        suggested_offer_low=offer_low,
        suggested_offer_high=offer_high,
        price_assessment=price_assess,
        value_assessment=value_assess,
        tips=tips,
    )


def format_advice(advice: OfferAdvice) -> str:
    """Render OfferAdvice as a human-readable report."""
    l = advice.listing
    lines = [
        "=" * 70,
        f"  PROPERTY: {l.address}",
        f"  ASKING PRICE: ${l.price:,}",
        f"  {l.bedrooms} bed / {l.bathrooms} bath / {l.sqft:,} sqft",
        "=" * 70,
        "",
        "MARKET POSITION",
        f"  Price assessment : {advice.price_assessment}",
        f"  Value assessment : {advice.value_assessment}",
        "",
        "SUGGESTED OFFER RANGE",
        f"  Low  : ${advice.suggested_offer_low:,}",
        f"  High : ${advice.suggested_offer_high:,}",
        "",
        "NEGOTIATION & PURCHASE TIPS",
    ]
    for i, tip in enumerate(advice.tips, 1):
        lines.append(f"  {i}. {tip}")
    lines.append("")
    if l.url:
        lines.append(f"  Listing URL: {l.url}")
    lines.append("=" * 70)
    return "\n".join(lines)
