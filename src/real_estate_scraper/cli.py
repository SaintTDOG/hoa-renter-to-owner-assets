"""Command-line interface for the real estate listing scraper."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import asdict

from .advisor import advise_on_listing, format_advice
from .analyzer import build_market_snapshot
from .models import Listing, ListingStatus
from .scraper import (
    BaseScraper,
    CraigslistScraper,
    RealtorDotComScraper,
    RedfinScraper,
    get_all_scrapers,
)

_SCRAPER_MAP: dict[str, type[BaseScraper]] = {
    "realtor": RealtorDotComScraper,
    "redfin": RedfinScraper,
    "craigslist": CraigslistScraper,
}


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="re-scraper",
        description="Scrape real estate listings and get purchase/negotiation advice.",
    )
    p.add_argument(
        "location",
        help="Location to search (e.g. 'Austin, TX' or 'Denver, CO').",
    )
    p.add_argument(
        "-s", "--source",
        choices=list(_SCRAPER_MAP.keys()) + ["all"],
        default="all",
        help="Which listing source to scrape (default: all).",
    )
    p.add_argument(
        "-n", "--max-results",
        type=int,
        default=20,
        help="Maximum number of listings to fetch per source (default: 20).",
    )
    p.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Delay in seconds between HTTP requests (default: 2.0).",
    )
    p.add_argument(
        "--advise",
        type=int,
        metavar="INDEX",
        default=None,
        help="Show detailed advice for listing at INDEX (0-based).",
    )
    p.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Output results as JSON.",
    )
    p.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging.",
    )
    return p


def _print_listing_table(listings: list[Listing]) -> None:
    """Print a compact table of listings."""
    if not listings:
        print("No listings found.")
        return

    header = f"{'#':>3}  {'Price':>12}  {'Bed':>3}  {'Bath':>4}  {'SqFt':>7}  {'$/SqFt':>8}  Address"
    print(header)
    print("-" * len(header))
    for i, l in enumerate(listings):
        ppsf = f"${l.price_per_sqft:,.0f}" if l.price_per_sqft else "—"
        sqft_s = f"{l.sqft:,}" if l.sqft else "—"
        print(
            f"{i:>3}  ${l.price:>11,}  {l.bedrooms:>3}  {l.bathrooms:>4.1f}  {sqft_s:>7}  {ppsf:>8}  {l.address}"
        )
    print(f"\nTotal: {len(listings)} listings")


def _print_market_summary(listings: list[Listing]) -> None:
    """Print aggregated market stats."""
    snap = build_market_snapshot(listings)
    if not snap:
        return
    print("\n--- Market Summary ---")
    print(f"  Median price       : ${snap.median_price:,}")
    print(f"  Median $/sqft      : ${snap.median_price_per_sqft:,.0f}")
    print(f"  Median sqft        : {snap.median_sqft:,}")
    print(f"  Price range        : ${snap.price_range[0]:,} – ${snap.price_range[1]:,}")
    print(f"  Active listings    : {snap.total_active_listings}")
    if snap.avg_days_on_market:
        print(f"  Avg days on market : {snap.avg_days_on_market:.0f}")
    print()


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    # Build scrapers
    kwargs = {"delay": args.delay}
    if args.source == "all":
        scrapers = get_all_scrapers(**kwargs)
    else:
        scrapers = [_SCRAPER_MAP[args.source](**kwargs)]

    # Scrape
    all_listings: list[Listing] = []
    for scraper in scrapers:
        print(f"Searching {scraper.name()} for '{args.location}' ...")
        results = scraper.search(args.location, max_results=args.max_results)
        all_listings.extend(results)

    if args.output_json:
        data = [asdict(l) for l in all_listings]
        for d in data:
            d["status"] = d["status"].value if hasattr(d["status"], "value") else d["status"]
        print(json.dumps(data, indent=2))
        return 0

    _print_listing_table(all_listings)
    _print_market_summary(all_listings)

    # Detailed advice for a specific listing
    if args.advise is not None:
        idx = args.advise
        if idx < 0 or idx >= len(all_listings):
            print(f"Error: index {idx} out of range (0–{len(all_listings) - 1}).", file=sys.stderr)
            return 1
        target = all_listings[idx]
        comparables = [l for l in all_listings if l is not target]
        advice = advise_on_listing(target, comparables)
        print(format_advice(advice))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
