"""Scraper implementations for Australian real estate listing sites."""

from __future__ import annotations

import logging
import re
import time
from abc import ABC, abstractmethod
from typing import Optional
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup, Tag

from .models import Listing, ListingStatus, PropertyType

logger = logging.getLogger(__name__)

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-AU,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Australian state/territory abbreviations
_AU_STATES = {"nsw", "vic", "qld", "wa", "sa", "tas", "act", "nt"}


_PRICE_FLOOR = 10_000


def _parse_price(text: Optional[str]) -> int:
    """Parse Australian price text, handling ranges, k/m suffixes, and junk."""
    if not text:
        return 0
    t = text.strip().lower()
    if any(kw in t for kw in ("contact", "enquire", "expression", "eoi", "poa", "auction")):
        return 0

    # Match first dollar-prefixed number with optional k/m suffix
    m = re.search(r"\$\s*([\d,]+(?:\.\d+)?)\s*([km])?", t)
    if not m:
        # Only try without dollar sign if text looks price-like (not dates, IDs, etc.)
        m = re.search(r"(?:^|[\s(])([\d,]+(?:\.\d+)?)\s*([km])", t)
    if not m:
        return 0

    raw = float(m.group(1).replace(",", ""))
    suffix = m.group(2)
    if suffix == "m":
        raw *= 1_000_000
    elif suffix == "k":
        raw *= 1_000

    price = int(raw)
    return price if price >= _PRICE_FLOOR else 0


def _safe_int(text: Optional[str], default: int = 0) -> int:
    """Extract an integer from text, stripping non-digit characters."""
    if not text:
        return default
    cleaned = re.sub(r"[^\d]", "", text)
    return int(cleaned) if cleaned else default


def _safe_float(text: Optional[str], default: float = 0.0) -> float:
    """Extract a float from text."""
    if not text:
        return default
    match = re.search(r"[\d]+\.?[\d]*", text.replace(",", ""))
    return float(match.group()) if match else default


def _guess_property_type(text: str) -> PropertyType:
    """Guess the property type from descriptive text."""
    lower = text.lower()
    if "apartment" in lower or "unit" in lower or "flat" in lower:
        return PropertyType.APARTMENT
    if "townhouse" in lower or "terrace" in lower:
        return PropertyType.TOWNHOUSE
    if "villa" in lower:
        return PropertyType.VILLA
    if "land" in lower or "vacant" in lower:
        return PropertyType.LAND
    if "rural" in lower or "acreage" in lower or "farm" in lower:
        return PropertyType.RURAL
    return PropertyType.HOUSE


class BaseScraper(ABC):
    """Abstract base class for all listing scrapers."""

    def __init__(self, *, delay: float = 2.0, timeout: int = 15) -> None:
        self.delay = delay
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(_DEFAULT_HEADERS)

    def _get(self, url: str) -> BeautifulSoup:
        """Fetch a URL and return parsed HTML."""
        time.sleep(self.delay)
        logger.info("Fetching %s", url)
        resp = self.session.get(url, timeout=self.timeout)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")

    @abstractmethod
    def search(self, location: str, *, max_results: int = 20) -> list[Listing]:
        """Search for listings in the given location."""

    @abstractmethod
    def name(self) -> str:
        """Human-readable name of this scraper source."""


class DomainScraper(BaseScraper):
    """Scraper for Domain.com.au search results pages."""

    _BASE = "https://www.domain.com.au/sale"

    def name(self) -> str:
        return "Domain.com.au"

    def _build_url(self, location: str) -> str:
        # Domain uses slugs like "melbourne-vic-3000" or "sydney-nsw-2000"
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", location.strip().lower()).strip("-")
        return f"{self._BASE}/{slug}/"

    def search(self, location: str, *, max_results: int = 20) -> list[Listing]:
        url = self._build_url(location)
        try:
            soup = self._get(url)
        except requests.RequestException as exc:
            logger.warning("Domain.com.au request failed: %s", exc)
            return []

        listings: list[Listing] = []
        # Domain uses data-testid attributes on listing cards
        cards = soup.select("[data-testid='listing-card-wrapper-premiumplus'],"
                           "[data-testid='listing-card-wrapper-premium'],"
                           "[data-testid='listing-card-wrapper-standard']")
        if not cards:
            cards = soup.select("div.listing-result")
        if not cards:
            cards = soup.select("[class*='listing-card']")

        for card in cards[:max_results]:
            listing = self._parse_card(card)
            if listing:
                listings.append(listing)

        logger.info("Domain.com.au returned %d listings for '%s'", len(listings), location)
        return listings

    def _parse_card(self, card: Tag) -> Optional[Listing]:
        try:
            price_el = card.select_one("[data-testid='listing-card-price'],"
                                       ".listing-result__price")
            price_text = price_el.get_text(strip=True) if price_el else ""
            price = _parse_price(price_text)
            if price == 0:
                return None

            addr_el = card.select_one("[data-testid='address-line1'],"
                                      ".listing-result__address")
            address = addr_el.get_text(strip=True) if addr_el else "Unknown"

            addr2_el = card.select_one("[data-testid='address-line2']")
            if addr2_el:
                address += ", " + addr2_el.get_text(strip=True)

            beds = 0
            baths = 0.0
            parking = 0
            feature_els = card.select("[data-testid='property-features-text-container'] span,"
                                      ".listing-result__features span")
            for feat in feature_els:
                text = feat.get_text(strip=True).lower()
                if "bed" in text:
                    beds = _safe_int(text)
                elif "bath" in text:
                    baths = _safe_float(text)
                elif "parking" in text or "car" in text:
                    parking = _safe_int(text)

            prop_type_el = card.select_one("[data-testid='listing-card-property-type']")
            prop_type_text = prop_type_el.get_text(strip=True) if prop_type_el else ""
            prop_type = _guess_property_type(prop_type_text or address)

            link_el = card.select_one("a[href]")
            detail_url = ""
            if link_el:
                href = link_el.get("href", "")
                if href.startswith("/"):
                    detail_url = f"https://www.domain.com.au{href}"
                elif href.startswith("http"):
                    detail_url = href

            # Check for auction
            status = ListingStatus.ACTIVE
            if "auction" in price_text.lower():
                status = ListingStatus.AUCTION

            return Listing(
                address=address,
                price=price,
                bedrooms=beds,
                bathrooms=baths,
                sqm=0,
                parking=parking,
                property_type=prop_type,
                status=status,
                url=detail_url,
            )
        except Exception as exc:
            logger.debug("Failed to parse Domain card: %s", exc)
            return None


class RealestateComAuScraper(BaseScraper):
    """Scraper for realestate.com.au search result pages."""

    _BASE = "https://www.realestate.com.au/buy/in-"

    def name(self) -> str:
        return "Realestate.com.au"

    def _build_url(self, location: str) -> str:
        # REA uses format like "melbourne,+vic+3000" or "sydney,+nsw+2000"
        parts = [p.strip() for p in location.split(",")]
        slug = "+".join(p.replace(" ", "+") for p in parts)
        return f"{self._BASE}{slug}/list-1"

    def search(self, location: str, *, max_results: int = 20) -> list[Listing]:
        url = self._build_url(location)
        try:
            soup = self._get(url)
        except requests.RequestException as exc:
            logger.warning("Realestate.com.au request failed: %s", exc)
            return []

        listings: list[Listing] = []
        cards = soup.select("[class*='residential-card']")
        if not cards:
            cards = soup.select("article.resultBody")
        if not cards:
            cards = soup.select("div.tiered-results--container article")

        for card in cards[:max_results]:
            listing = self._parse_card(card)
            if listing:
                listings.append(listing)

        logger.info("Realestate.com.au returned %d listings for '%s'",
                     len(listings), location)
        return listings

    def _parse_card(self, card: Tag) -> Optional[Listing]:
        try:
            price_el = card.select_one("[class*='property-price'],"
                                       ".card__price,"
                                       "span.price")
            price_text = price_el.get_text(strip=True) if price_el else ""
            price = _parse_price(price_text)
            if price == 0:
                return None

            addr_el = card.select_one("[class*='address'],"
                                      ".card__address,"
                                      "h2.card__title a")
            address = addr_el.get_text(strip=True) if addr_el else "Unknown"

            text = card.get_text(strip=True).lower()
            beds = 0
            baths = 0.0
            parking = 0
            sqm = 0

            beds_m = re.search(r"(\d+)\s*bed", text)
            if beds_m:
                beds = int(beds_m.group(1))
            baths_m = re.search(r"([\d.]+)\s*bath", text)
            if baths_m:
                baths = float(baths_m.group(1))
            car_m = re.search(r"(\d+)\s*car", text)
            if car_m:
                parking = int(car_m.group(1))
            sqm_m = re.search(r"([\d,]+)\s*m[²2]", text)
            if sqm_m:
                sqm = _safe_int(sqm_m.group(1))

            prop_type = _guess_property_type(text)

            link_el = card.select_one("a[href]")
            detail_url = ""
            if link_el:
                href = link_el.get("href", "")
                if href.startswith("/"):
                    detail_url = f"https://www.realestate.com.au{href}"
                elif href.startswith("http"):
                    detail_url = href

            status = ListingStatus.ACTIVE
            if "auction" in price_text.lower():
                status = ListingStatus.AUCTION
            elif "under offer" in price_text.lower():
                status = ListingStatus.UNDER_OFFER

            return Listing(
                address=address,
                price=price,
                bedrooms=beds,
                bathrooms=baths,
                sqm=sqm,
                parking=parking,
                property_type=prop_type,
                status=status,
                url=detail_url,
            )
        except Exception as exc:
            logger.debug("Failed to parse REA card: %s", exc)
            return None


class GumtreeScraper(BaseScraper):
    """Scraper for Gumtree Australia real estate for sale pages."""

    def name(self) -> str:
        return "Gumtree.com.au"

    def _build_url(self, location: str) -> str:
        query = quote_plus(location.strip())
        return f"https://www.gumtree.com.au/s-property/k0?search_query={query}"

    def search(self, location: str, *, max_results: int = 20) -> list[Listing]:
        url = self._build_url(location)
        try:
            soup = self._get(url)
        except requests.RequestException as exc:
            logger.warning("Gumtree request failed: %s", exc)
            return []

        listings: list[Listing] = []
        rows = soup.select("a.user-ad-row, div.user-ad-collection-new-design__wrapper--row")
        if not rows:
            rows = soup.select("[class*='ad-listing']")

        for row in rows[:max_results]:
            listing = self._parse_row(row)
            if listing:
                listings.append(listing)

        logger.info("Gumtree returned %d listings for '%s'", len(listings), location)
        return listings

    def _parse_row(self, row: Tag) -> Optional[Listing]:
        try:
            price_el = row.select_one("[class*='price'], .user-ad-price")
            price = _parse_price(price_el.get_text() if price_el else None)
            if price == 0:
                return None

            title_el = row.select_one("[class*='title'], .user-ad-row-new-design__title-span")
            title = title_el.get_text(strip=True) if title_el else "Unknown"

            link_el = row.select_one("a[href]")
            detail_url = ""
            if link_el:
                href = link_el.get("href", "")
                if href.startswith("/"):
                    detail_url = f"https://www.gumtree.com.au{href}"
                elif href.startswith("http"):
                    detail_url = href

            text = row.get_text(strip=True).lower()
            beds_m = re.search(r"(\d+)\s*bed", text)
            beds = int(beds_m.group(1)) if beds_m else 0
            baths_m = re.search(r"([\d.]+)\s*bath", text)
            baths = float(baths_m.group(1)) if baths_m else 0.0
            sqm_m = re.search(r"([\d,]+)\s*m[²2]", text)
            sqm = _safe_int(sqm_m.group(1)) if sqm_m else 0

            return Listing(
                address=title,
                price=price,
                bedrooms=beds,
                bathrooms=baths,
                sqm=sqm,
                url=detail_url,
            )
        except Exception as exc:
            logger.debug("Failed to parse Gumtree row: %s", exc)
            return None


def get_all_scrapers(**kwargs) -> list[BaseScraper]:
    """Return instances of all available scrapers."""
    return [
        DomainScraper(**kwargs),
        RealestateComAuScraper(**kwargs),
        GumtreeScraper(**kwargs),
    ]
