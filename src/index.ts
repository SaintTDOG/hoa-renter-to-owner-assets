import { Env, DailyDigest, PropertyUpdate, ScrapeError, AustralianState } from './types';
import { SOURCES } from './sources';
import { scrapeSource } from './scraper';
import { storeDailyDigest, getLatestDigest, getDigestByDate, listDigestDates, filterNewUpdates } from './storage';
import { generateAllContent, generateEmail, generateXPost, generateFacebookPost, DEFAULT_CONFIG } from './content';

const ALL_STATES: AustralianState[] = ['NSW', 'VIC', 'QLD', 'SA', 'WA', 'TAS', 'NT', 'ACT'];

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

export default {
  /**
   * HTTP request handler - serves the API.
   */
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: CORS_HEADERS });
    }

    // Route: GET /
    if (url.pathname === '/') {
      return jsonResponse({
        service: 'AU Property Law Scraper',
        description: 'Daily Australian property law updates for first home buyers',
        endpoints: {
          '/api/updates': 'Latest daily digest of property law updates',
          '/api/updates/:date': 'Digest for a specific date (YYYY-MM-DD)',
          '/api/updates/state/:state': 'Latest updates filtered by state',
          '/api/dates': 'List of available digest dates',
          '/api/scrape': 'Trigger a manual scrape (POST)',
          '/api/content': 'CRO-optimized content for all channels (email, X, Facebook)',
          '/api/content/email': 'Email newsletter HTML and plain text',
          '/api/content/x': 'X (Twitter) post and thread content',
          '/api/content/facebook': 'Facebook post content',
        },
        states: ALL_STATES,
        cronSchedule: 'Daily at 6:00 AM AEST',
      });
    }

    // Route: GET /api/updates
    if (url.pathname === '/api/updates') {
      const digest = await getLatestDigest(env);
      if (!digest) {
        return jsonResponse({ message: 'No digests available yet. Scraping runs daily at 6 AM AEST.' }, 404);
      }
      return jsonResponse(formatDigestResponse(digest));
    }

    // Route: GET /api/updates/state/:state
    const stateMatch = url.pathname.match(/^\/api\/updates\/state\/([A-Za-z]+)$/);
    if (stateMatch) {
      const state = stateMatch[1].toUpperCase() as AustralianState;
      if (!ALL_STATES.includes(state)) {
        return jsonResponse({ error: `Invalid state. Valid: ${ALL_STATES.join(', ')}` }, 400);
      }
      const digest = await getLatestDigest(env);
      if (!digest) {
        return jsonResponse({ message: 'No digests available yet.' }, 404);
      }
      const filtered: DailyDigest = {
        ...digest,
        updates: digest.updates.filter((u) => u.state === state),
        errors: digest.errors.filter((e) => e.state === state),
      };
      return jsonResponse(formatDigestResponse(filtered));
    }

    // Route: GET /api/updates/:date
    const dateMatch = url.pathname.match(/^\/api\/updates\/(\d{4}-\d{2}-\d{2})$/);
    if (dateMatch) {
      const digest = await getDigestByDate(env, dateMatch[1]);
      if (!digest) {
        return jsonResponse({ error: `No digest found for ${dateMatch[1]}` }, 404);
      }
      return jsonResponse(formatDigestResponse(digest));
    }

    // Route: GET /api/dates
    if (url.pathname === '/api/dates') {
      const dates = await listDigestDates(env);
      return jsonResponse({ dates, count: dates.length });
    }

    // Route: GET /api/content - all channel content
    if (url.pathname === '/api/content') {
      const digest = await getLatestDigest(env);
      if (!digest) {
        return jsonResponse({ message: 'No digests available yet.' }, 404);
      }
      const content = generateAllContent(digest);
      return jsonResponse(content);
    }

    // Route: GET /api/content/email - email newsletter
    if (url.pathname === '/api/content/email') {
      const digest = await getLatestDigest(env);
      if (!digest) {
        return jsonResponse({ message: 'No digests available yet.' }, 404);
      }
      const format = url.searchParams.get('format');
      const email = generateEmail(digest, DEFAULT_CONFIG);
      if (format === 'html') {
        return new Response(email.html, {
          headers: { 'Content-Type': 'text/html', ...CORS_HEADERS },
        });
      }
      return jsonResponse(email);
    }

    // Route: GET /api/content/x - X/Twitter post
    if (url.pathname === '/api/content/x') {
      const digest = await getLatestDigest(env);
      if (!digest) {
        return jsonResponse({ message: 'No digests available yet.' }, 404);
      }
      return jsonResponse(generateXPost(digest, DEFAULT_CONFIG));
    }

    // Route: GET /api/content/facebook - Facebook post
    if (url.pathname === '/api/content/facebook') {
      const digest = await getLatestDigest(env);
      if (!digest) {
        return jsonResponse({ message: 'No digests available yet.' }, 404);
      }
      return jsonResponse(generateFacebookPost(digest, DEFAULT_CONFIG));
    }

    // Route: POST /api/scrape (manual trigger)
    if (url.pathname === '/api/scrape' && request.method === 'POST') {
      const digest = await runScrape(env);
      return jsonResponse({
        message: 'Scrape completed',
        updatesFound: digest.updates.length,
        statesScraped: digest.statesScraped.length,
        errors: digest.errors.length,
      });
    }

    return jsonResponse({ error: 'Not found' }, 404);
  },

  /**
   * Cron trigger handler - runs the daily scrape.
   */
  async scheduled(_event: ScheduledEvent, env: Env, ctx: ExecutionContext): Promise<void> {
    ctx.waitUntil(runScrape(env));
  },
};

/**
 * Main scrape orchestrator. Scrapes all sources, filters for relevance
 * and novelty, then stores the daily digest.
 */
async function runScrape(env: Env): Promise<DailyDigest> {
  const today = new Date().toISOString().split('T')[0];
  const allUpdates: PropertyUpdate[] = [];
  const allErrors: ScrapeError[] = [];
  const scrapedStates = new Set<AustralianState>();

  // Scrape sources in batches of 4 to avoid overwhelming workers limits
  const batchSize = 4;
  for (let i = 0; i < SOURCES.length; i += batchSize) {
    const batch = SOURCES.slice(i, i + batchSize);
    const results = await Promise.allSettled(batch.map((source) => scrapeSource(source)));

    for (let j = 0; j < results.length; j++) {
      const source = batch[j];
      const result = results[j];
      scrapedStates.add(source.state);

      if (result.status === 'fulfilled') {
        allUpdates.push(...result.value.updates);
        if (result.value.error) {
          allErrors.push(result.value.error);
        }
      } else {
        allErrors.push({
          state: source.state,
          source: source.name,
          error: result.reason?.message || 'Unknown error',
        });
      }
    }
  }

  // Filter to only new updates (not seen in past 7 days)
  const newUpdates = await filterNewUpdates(env, allUpdates);

  // Sort by relevance score
  newUpdates.sort((a, b) => b.relevanceScore - a.relevanceScore);

  const digest: DailyDigest = {
    date: today,
    updates: newUpdates,
    statesScraped: [...scrapedStates],
    errors: allErrors,
  };

  await storeDailyDigest(env, digest);
  console.log(
    `[${today}] Scrape complete: ${newUpdates.length} new updates, ${allErrors.length} errors`
  );

  return digest;
}

/**
 * Formats a digest for API response with summary statistics.
 */
function formatDigestResponse(digest: DailyDigest) {
  const byState: Record<string, number> = {};
  const byCategory: Record<string, number> = {};

  for (const update of digest.updates) {
    byState[update.state] = (byState[update.state] || 0) + 1;
    byCategory[update.category] = (byCategory[update.category] || 0) + 1;
  }

  return {
    date: digest.date,
    summary: {
      totalUpdates: digest.updates.length,
      statesScraped: digest.statesScraped.length,
      errorCount: digest.errors.length,
      updatesByState: byState,
      updatesByCategory: byCategory,
    },
    updates: digest.updates,
    errors: digest.errors.length > 0 ? digest.errors : undefined,
  };
}

function jsonResponse(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data, null, 2), {
    status,
    headers: {
      'Content-Type': 'application/json',
      ...CORS_HEADERS,
    },
  });
}
