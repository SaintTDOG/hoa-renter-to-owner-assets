"""Data models for real estate listings."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ListingStatus(Enum):
    ACTIVE = "active"
    PENDING = "pending"
    SOLD = "sold"
    UNKNOWN = "unknown"


@dataclass
class Listing:
    """A single real estate listing."""

    address: str
    price: int
    bedrooms: int
    bathrooms: float
    sqft: int
    lot_sqft: Optional[int] = None
    year_built: Optional[int] = None
    status: ListingStatus = ListingStatus.ACTIVE
    property_type: str = "single_family"
    url: str = ""
    description: str = ""
    days_on_market: Optional[int] = None
    price_per_sqft: Optional[float] = None
    hoa_fee: Optional[int] = None
    taxes_annual: Optional[int] = None
    extras: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.sqft > 0 and self.price_per_sqft is None:
            self.price_per_sqft = round(self.price / self.sqft, 2)


@dataclass
class MarketSnapshot:
    """Aggregated market data for a set of comparable listings."""

    median_price: int
    median_price_per_sqft: float
    avg_days_on_market: float
    total_active_listings: int
    price_range: tuple[int, int]
    median_sqft: int
