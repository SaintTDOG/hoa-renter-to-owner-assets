"""Data models for Australian real estate listings."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ListingStatus(Enum):
    ACTIVE = "active"
    UNDER_OFFER = "under_offer"
    SOLD = "sold"
    AUCTION = "auction"
    UNKNOWN = "unknown"


class PropertyType(Enum):
    HOUSE = "house"
    APARTMENT = "apartment"
    TOWNHOUSE = "townhouse"
    VILLA = "villa"
    LAND = "land"
    RURAL = "rural"
    OTHER = "other"


@dataclass
class Listing:
    """A single Australian real estate listing."""

    address: str
    price: int  # AUD
    bedrooms: int
    bathrooms: float
    sqm: int  # square metres (internal / building area)
    land_sqm: Optional[int] = None
    year_built: Optional[int] = None
    status: ListingStatus = ListingStatus.ACTIVE
    property_type: PropertyType = PropertyType.HOUSE
    url: str = ""
    description: str = ""
    days_on_market: Optional[int] = None
    price_per_sqm: Optional[float] = None
    strata_levy: Optional[int] = None  # quarterly strata/body-corp levy
    council_rates: Optional[int] = None  # annual council rates
    parking: Optional[int] = None  # number of car spaces
    auction_date: Optional[str] = None
    extras: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.sqm > 0 and self.price_per_sqm is None:
            self.price_per_sqm = round(self.price / self.sqm, 2)


@dataclass
class MarketSnapshot:
    """Aggregated market data for a set of comparable listings."""

    median_price: int
    median_price_per_sqm: float
    avg_days_on_market: float
    total_active_listings: int
    price_range: tuple[int, int]
    median_sqm: int
