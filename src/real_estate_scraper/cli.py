"""Command-line interface for the Australian real estate listing scraper."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import asdict

from .advisor import advise_on_listing, format_advice
from .analyzer import build_market_snapshot
from .models import Listing
from .scraper import (
    BaseScraper,
    DomainScraper,
    GumtreeScraper,
    RealestateComAuScraper,
    get_all_scrapers,
)

_SCRAPER_MAP: dict[str, type[BaseScraper]] = {
    "domain": DomainScraper,
    "rea": RealestateComAuScraper,
    "gumtree": GumtreeScraper,
}


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="re-scraper",
        description=(
            "Scrape Australian real estate listings and get "
            "purchase/negotiation advice."
        ),
    )
    p.add_argument(
        "location",
        help="Location to search (e.g. 'Melbourne, VIC' or 'Sydney, NSW 2000').",
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

    header = (f"{'#':>3}  {'Price (AUD)':>14}  {'Bed':>3}  {'Bath':>4}  "
              f"{'m²':>6}  {'$/m²':>9}  {'Car':>3}  Address")
    print(header)
    print("-" * len(header))
    for i, l in enumerate(listings):
        ppsm = f"${l.price_per_sqm:,.0f}" if l.price_per_sqm else "—"
        sqm_s = f"{l.sqm:,}" if l.sqm else "—"
        car_s = str(l.parking) if l.parking else "—"
        print(
            f"{i:>3}  ${l.price:>13,}  {l.bedrooms:>3}  {l.bathrooms:>4.0f}  "
            f"{sqm_s:>6}  {ppsm:>9}  {car_s:>3}  {l.address}"
        )
    print(f"\nTotal: {len(listings)} listings")


def _print_market_summary(listings: list[Listing]) -> None:
    """Print aggregated market stats."""
    snap = build_market_snapshot(listings)
    if not snap:
        return
    print("\n--- Market Summary (AUD) ---")
    print(f"  Median price       : ${snap.median_price:,}")
    print(f"  Median $/m²        : ${snap.median_price_per_sqm:,.0f}")
    print(f"  Median m²          : {snap.median_sqm:,}")
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
            # Serialize enums to their string values
            for key in ("status", "property_type"):
                if hasattr(d.get(key), "value"):
                    d[key] = d[key].value
        print(json.dumps(data, indent=2))
        return 0

    _print_listing_table(all_listings)
    _print_market_summary(all_listings)

    # Detailed advice for a specific listing
    if args.advise is not None:
        idx = args.advise
        if idx < 0 or idx >= len(all_listings):
            print(f"Error: index {idx} out of range (0–{len(all_listings) - 1}).",
                  file=sys.stderr)
            return 1
        target = all_listings[idx]
        comparables = [l for l in all_listings if l is not target]
        advice = advise_on_listing(target, comparables)
        print(format_advice(advice))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
