/**
 * Cloudflare Worker integration example for PropertyIQ "Should I Buy?" feature.
 *
 * Set the SCRAPER_API_URL secret in your Worker:
 *   wrangler secret put SCRAPER_API_URL
 *   → https://propertyiq-scraper.fly.dev  (or wherever you deploy the Python API)
 */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // Only handle the /should-i-buy path
    if (url.pathname !== "/should-i-buy") {
      return new Response("Not found", { status: 404 });
    }

    const location = url.searchParams.get("location");
    const index = url.searchParams.get("index") ?? "0";
    const source = url.searchParams.get("source") ?? "all";

    if (!location) {
      return Response.json(
        { error: "Missing required 'location' parameter (e.g. ?location=Melbourne,+VIC)" },
        { status: 400 }
      );
    }

    const apiBase = env.SCRAPER_API_URL || "http://localhost:8000";
    const apiUrl = new URL("/api/should-i-buy", apiBase);
    apiUrl.searchParams.set("location", location);
    apiUrl.searchParams.set("index", index);
    apiUrl.searchParams.set("source", source);

    try {
      const resp = await fetch(apiUrl.toString(), {
        headers: { "Accept": "application/json" },
      });

      if (!resp.ok) {
        const body = await resp.text();
        return Response.json(
          { error: `Scraper API returned ${resp.status}`, detail: body },
          { status: resp.status }
        );
      }

      const data = await resp.json();

      // Return a simplified response for the frontend
      return Response.json({
        verdict: data.verdict,
        listing: {
          address: data.listing.address,
          price: data.listing.price,
          bedrooms: data.listing.bedrooms,
          bathrooms: data.listing.bathrooms,
          sqm: data.listing.sqm,
          parking: data.listing.parking,
          property_type: data.listing.property_type,
          url: data.listing.url,
        },
        offer_range: {
          low: data.advice.suggested_offer_low,
          high: data.advice.suggested_offer_high,
        },
        price_assessment: data.advice.price_assessment,
        value_assessment: data.advice.value_assessment,
        tips: data.advice.tips,
        market_summary: data.market_summary,
      }, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Cache-Control": "public, max-age=300",  // Cache 5 min
        },
      });
    } catch (err) {
      return Response.json(
        { error: "Failed to reach scraper API", detail: err.message },
        { status: 502 }
      );
    }
  },
};
