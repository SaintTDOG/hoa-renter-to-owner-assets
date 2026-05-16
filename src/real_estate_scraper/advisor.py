"""Negotiation and purchase advisor — generates Australia-specific advice."""

from __future__ import annotations

from dataclasses import dataclass, field

from .analyzer import build_market_snapshot, price_position, sqm_value_position
from .models import Listing, ListingStatus, MarketSnapshot, PropertyType


@dataclass
class OfferAdvice:
    """Structured negotiation advice for a single listing."""

    listing: Listing
    suggested_offer_low: int
    suggested_offer_high: int
    price_assessment: str
    value_assessment: str
    tips: list[str] = field(default_factory=list)


# --- Tip generators ---


def _dom_tips(listing: Listing) -> list[str]:
    """Generate tips based on days-on-market."""
    dom = listing.days_on_market
    if dom is None:
        return ["Ask the agent how long the property has been on the market."]

    if listing.status == ListingStatus.AUCTION:
        if dom > 60:
            return [
                f"This property has been listed for {dom} days before auction — "
                "check if the auction was rescheduled and why.",
            ]
        return []

    if dom > 90:
        return [
            f"This listing has been on the market for {dom} days — the vendor may be motivated.",
            "There is likely room to negotiate well below the guide price.",
            "Ask the agent if there have been previous price reductions.",
        ]
    if dom > 45:
        return [
            f"On the market for {dom} days — moderate time, some negotiation room likely.",
            "Consider starting 5–8% below the asking/guide price.",
        ]
    if dom > 14:
        return [
            f"Listed for {dom} days — still relatively fresh.",
            "A competitive offer 2–5% below the guide price is reasonable.",
        ]
    return [
        f"Only {dom} days on market — this is a fresh listing.",
        "In a competitive market, consider offering at or near the guide price.",
        "If you really want this property, a strong initial offer reduces the risk of losing it.",
    ]


def _auction_tips(listing: Listing) -> list[str]:
    """Tips specific to auction sales (very common in Australia)."""
    if listing.status != ListingStatus.AUCTION:
        return []
    tips = [
        "This property is going to auction — there is no cooling-off period at auction.",
        "Get your building & pest inspection done BEFORE auction day.",
        "Ensure your finance is unconditionally approved before bidding.",
        "Set a firm maximum bid and stick to it on the day.",
        "Register to bid early and bring valid ID.",
    ]
    if listing.auction_date:
        tips.insert(0, f"Auction date: {listing.auction_date}.")
    return tips


def _strata_tips(listing: Listing) -> list[str]:
    """Tips for strata/body corporate properties (apartments, townhouses)."""
    is_strata = listing.property_type in (
        PropertyType.APARTMENT, PropertyType.TOWNHOUSE, PropertyType.VILLA
    )
    if not is_strata and listing.strata_levy is None:
        return []
    tips = []
    if listing.strata_levy is not None and listing.strata_levy > 0:
        tips.append(
            f"Strata levy is ${listing.strata_levy:,}/quarter — factor this into your budget."
        )
    if is_strata:
        tips.extend([
            "Request a strata/body corporate report — the name varies by state "
            "(e.g. Section 184 certificate in NSW, Owners Corporation certificate in VIC, "
            "Body Corporate Information Certificate in QLD).",
            "Check the sinking fund balance — a low balance may mean future special levies.",
            "Review strata meeting minutes for disputes, planned works, or building defects.",
        ])
    else:
        tips.append("This property has a body corporate levy — request details of what it covers.")
    return tips


def _stamp_duty_tips(listing: Listing) -> list[str]:
    """Tips about stamp duty (transfer duty) — a major cost in Australia."""
    price = listing.price
    tips = [
        f"Budget for stamp duty (transfer duty) on top of the ${price:,} purchase price.",
        "First home buyers may be eligible for stamp duty concessions or exemptions — "
        "check your state's revenue office.",
        "Foreign buyers face surcharge stamp duty in most states (up to 9% extra in NSW). "
        "Rates vary by state.",
    ]
    return tips


def _general_purchase_tips() -> list[str]:
    """General Australian property purchase tips."""
    return [
        "Always get a building & pest inspection before making an unconditional offer.",
        "Engage a conveyancer or solicitor early to review the Contract of Sale "
        "and vendor disclosure documents (e.g. Section 32 in VIC).",
        "Get unconditional finance approval (not just pre-approval) to strengthen your offer.",
        "Understand the cooling-off period in your state — they vary from none (WA, TAS) to "
        "5 business days (NSW, QLD, ACT). VIC has 3 clear business days. "
        "Check with your conveyancer.",
        "Research the suburb: check median prices on Domain/REA, school zones, flood maps, "
        "and council planning.",
        "Factor in all purchase costs: stamp duty, conveyancing, building & pest, "
        "mortgage registration, and moving.",
        "If buying at auction, there is NO cooling-off period — all inspections and finance "
        "must be done beforehand.",
        "Check if the property is affected by easements, covenants, or heritage overlays.",
    ]


def _offer_range(listing: Listing, snapshot: MarketSnapshot | None) -> tuple[int, int]:
    """Calculate suggested offer range based on market position."""
    if snapshot and snapshot.median_price > 0:
        pct_diff = (listing.price - snapshot.median_price) / snapshot.median_price

        if pct_diff > 0.15:
            low_pct, high_pct = 0.85, 0.93
        elif pct_diff > 0.05:
            low_pct, high_pct = 0.90, 0.97
        elif pct_diff < -0.10:
            low_pct, high_pct = 0.95, 1.0
        else:
            low_pct, high_pct = 0.92, 0.98
    else:
        low_pct, high_pct = 0.90, 0.97

    dom = listing.days_on_market
    if dom is not None and dom > 60:
        low_pct -= 0.03
        high_pct -= 0.02

    if listing.status == ListingStatus.AUCTION:
        low_pct = (low_pct + 0.95) / 2
        high_pct = max(high_pct, 1.0)

    low = int(listing.price * low_pct)
    high = int(listing.price * high_pct)
    return low, high


def advise_on_listing(listing: Listing, comparables: list[Listing]) -> OfferAdvice:
    """Generate comprehensive negotiation advice for a listing."""
    snapshot = build_market_snapshot(comparables)
    price_assess = price_position(listing, snapshot) if snapshot else "no comparables available"
    value_assess = sqm_value_position(listing, snapshot) if snapshot else "no comparables available"
    offer_low, offer_high = _offer_range(listing, snapshot)

    tips: list[str] = []
    tips.extend(_dom_tips(listing))
    tips.extend(_auction_tips(listing))
    tips.extend(_strata_tips(listing))
    tips.extend(_stamp_duty_tips(listing))
    tips.extend(_general_purchase_tips())

    return OfferAdvice(
        listing=listing,
        suggested_offer_low=offer_low,
        suggested_offer_high=offer_high,
        price_assessment=price_assess,
        value_assessment=value_assess,
        tips=tips,
    )


def _format_bathrooms(value: float) -> str:
    if value == int(value):
        return str(int(value))
    return f"{value:g}"


def format_advice(advice: OfferAdvice) -> str:
    """Render OfferAdvice as a human-readable report."""
    l = advice.listing
    sqm_str = f"{l.sqm:,} m²" if l.sqm else "—"
    parking_str = f" / {l.parking} car" if l.parking else ""
    prop_type = l.property_type.value.replace("_", " ").title()
    bath_str = _format_bathrooms(l.bathrooms)
    lines = [
        "=" * 70,
        f"  PROPERTY: {l.address}",
        f"  GUIDE PRICE: ${l.price:,} AUD",
        f"  {l.bedrooms} bed / {bath_str} bath{parking_str} / {sqm_str}",
        f"  Type: {prop_type}",
        "=" * 70,
        "",
        "MARKET POSITION",
        f"  Price assessment : {advice.price_assessment}",
        f"  Value assessment : {advice.value_assessment}",
        "",
        "SUGGESTED OFFER RANGE",
        f"  Low  : ${advice.suggested_offer_low:,} AUD",
        f"  High : ${advice.suggested_offer_high:,} AUD",
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
