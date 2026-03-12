"""Scraper implementations for real estate listing sites."""

from __future__ import annotations

import logging
import re
import time
from abc import ABC, abstractmethod
from typing import Optional
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup, Tag

from .models import Listing, ListingStatus

logger = logging.getLogger(__name__)

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


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


class RealtorDotComScraper(BaseScraper):
    """Scraper for Realtor.com search results pages."""

    _BASE = "https://www.realtor.com/realestateandhomes-search"

    def name(self) -> str:
        return "Realtor.com"

    def _build_url(self, location: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", location.strip()).strip("-")
        return f"{self._BASE}/{slug}"

    def search(self, location: str, *, max_results: int = 20) -> list[Listing]:
        url = self._build_url(location)
        try:
            soup = self._get(url)
        except requests.RequestException as exc:
            logger.warning("Realtor.com request failed: %s", exc)
            return []

        listings: list[Listing] = []
        cards = soup.select("[data-testid='property-card']")
        if not cards:
            cards = soup.select("div.BasePropertyCard_propertyCardWrap__J0xUj")
        if not cards:
            cards = soup.select("li[data-testid='result-card']")

        for card in cards[:max_results]:
            listing = self._parse_card(card, source_url=url)
            if listing:
                listings.append(listing)

        logger.info("Realtor.com returned %d listings for '%s'", len(listings), location)
        return listings

    def _parse_card(self, card: Tag, source_url: str) -> Optional[Listing]:
        try:
            price_el = card.select_one("[data-testid='card-price']")
            price = _safe_int(price_el.get_text() if price_el else None)
            if price == 0:
                return None

            addr_el = card.select_one("[data-testid='card-address-1']")
            address = addr_el.get_text(strip=True) if addr_el else "Unknown"

            addr2_el = card.select_one("[data-testid='card-address-2']")
            if addr2_el:
                address += ", " + addr2_el.get_text(strip=True)

            beds = 0
            baths = 0.0
            sqft = 0
            meta_els = card.select("li[data-testid='property-meta-beds'],"
                                   "li[data-testid='property-meta-baths'],"
                                   "li[data-testid='property-meta-sqft']")
            for meta in meta_els:
                text = meta.get_text(strip=True).lower()
                if "bed" in text:
                    beds = _safe_int(text)
                elif "bath" in text:
                    baths = _safe_float(text)
                elif "sqft" in text or "sq" in text:
                    sqft = _safe_int(text)

            link_el = card.select_one("a[href]")
            detail_url = ""
            if link_el:
                href = link_el.get("href", "")
                if href.startswith("/"):
                    detail_url = f"https://www.realtor.com{href}"
                elif href.startswith("http"):
                    detail_url = href

            return Listing(
                address=address,
                price=price,
                bedrooms=beds,
                bathrooms=baths,
                sqft=sqft,
                url=detail_url,
            )
        except Exception as exc:
            logger.debug("Failed to parse card: %s", exc)
            return None


class RedfinScraper(BaseScraper):
    """Scraper for Redfin search result pages."""

    _BASE = "https://www.redfin.com/city"

    def name(self) -> str:
        return "Redfin"

    def _build_url(self, location: str) -> str:
        parts = [p.strip() for p in location.split(",")]
        if len(parts) >= 2:
            state = parts[-1].strip().upper()
            city = re.sub(r"[^a-zA-Z0-9]+", "-", parts[0].strip()).strip("-")
            return f"https://www.redfin.com/city/{city}-{state}/filter/include=sold-3mo"
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", location.strip()).strip("-")
        return f"https://www.redfin.com/city/{slug}"

    def search(self, location: str, *, max_results: int = 20) -> list[Listing]:
        url = self._build_url(location)
        try:
            soup = self._get(url)
        except requests.RequestException as exc:
            logger.warning("Redfin request failed: %s", exc)
            return []

        listings: list[Listing] = []
        cards = soup.select(".HomeCardContainer")
        if not cards:
            cards = soup.select("[data-rf-test-id='photo-card']")

        for card in cards[:max_results]:
            listing = self._parse_card(card)
            if listing:
                listings.append(listing)

        logger.info("Redfin returned %d listings for '%s'", len(listings), location)
        return listings

    def _parse_card(self, card: Tag) -> Optional[Listing]:
        try:
            price_el = card.select_one(".homecardV2Price, .HomeCardContainer--price")
            price = _safe_int(price_el.get_text() if price_el else None)
            if price == 0:
                return None

            addr_el = card.select_one(".homeAddressV2, .HomeCardContainer--address")
            address = addr_el.get_text(strip=True) if addr_el else "Unknown"

            stats_text = card.get_text(strip=True).lower()
            beds = 0
            baths = 0.0
            sqft = 0

            beds_m = re.search(r"(\d+)\s*bed", stats_text)
            if beds_m:
                beds = int(beds_m.group(1))
            baths_m = re.search(r"([\d.]+)\s*bath", stats_text)
            if baths_m:
                baths = float(baths_m.group(1))
            sqft_m = re.search(r"([\d,]+)\s*sq\s*ft", stats_text)
            if sqft_m:
                sqft = _safe_int(sqft_m.group(1))

            link_el = card.select_one("a[href]")
            detail_url = ""
            if link_el:
                href = link_el.get("href", "")
                if href.startswith("/"):
                    detail_url = f"https://www.redfin.com{href}"
                elif href.startswith("http"):
                    detail_url = href

            return Listing(
                address=address,
                price=price,
                bedrooms=beds,
                bathrooms=baths,
                sqft=sqft,
                url=detail_url,
            )
        except Exception as exc:
            logger.debug("Failed to parse Redfin card: %s", exc)
            return None


class CraigslistScraper(BaseScraper):
    """Scraper for Craigslist housing/real estate for sale pages."""

    def name(self) -> str:
        return "Craigslist"

    def _build_url(self, location: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "", location.strip().lower())
        return f"https://{slug}.craigslist.org/search/rea"

    def search(self, location: str, *, max_results: int = 20) -> list[Listing]:
        url = self._build_url(location)
        try:
            soup = self._get(url)
        except requests.RequestException as exc:
            logger.warning("Craigslist request failed: %s", exc)
            return []

        listings: list[Listing] = []
        rows = soup.select("li.cl-static-search-result, li.result-row")

        for row in rows[:max_results]:
            listing = self._parse_row(row)
            if listing:
                listings.append(listing)

        logger.info("Craigslist returned %d listings for '%s'", len(listings), location)
        return listings

    def _parse_row(self, row: Tag) -> Optional[Listing]:
        try:
            price_el = row.select_one(".priceinfo, .result-price")
            price = _safe_int(price_el.get_text() if price_el else None)
            if price == 0:
                return None

            title_el = row.select_one(".title, .result-title")
            title = title_el.get_text(strip=True) if title_el else "Unknown"

            link_el = row.select_one("a[href]")
            detail_url = ""
            if link_el:
                href = link_el.get("href", "")
                if href.startswith("http"):
                    detail_url = href

            text = row.get_text(strip=True).lower()
            beds_m = re.search(r"(\d+)\s*br", text)
            beds = int(beds_m.group(1)) if beds_m else 0
            sqft_m = re.search(r"([\d,]+)\s*ft", text)
            sqft = _safe_int(sqft_m.group(1)) if sqft_m else 0

            return Listing(
                address=title,
                price=price,
                bedrooms=beds,
                bathrooms=0,
                sqft=sqft,
                url=detail_url,
            )
        except Exception as exc:
            logger.debug("Failed to parse Craigslist row: %s", exc)
            return None


def get_all_scrapers(**kwargs) -> list[BaseScraper]:
    """Return instances of all available scrapers."""
    return [
        RealtorDotComScraper(**kwargs),
        RedfinScraper(**kwargs),
        CraigslistScraper(**kwargs),
    ]
