import { Env, DailyDigest, PropertyUpdate } from './types';

const DIGEST_PREFIX = 'digest:';
const LATEST_KEY = 'latest-digest';
const HISTORY_INDEX_KEY = 'digest-index';

/**
 * Stores a daily digest in KV.
 */
export async function storeDailyDigest(env: Env, digest: DailyDigest): Promise<void> {
  const key = `${DIGEST_PREFIX}${digest.date}`;

  // Store the digest with 90-day expiration
  await env.PROPERTY_UPDATES.put(key, JSON.stringify(digest), {
    expirationTtl: 90 * 24 * 60 * 60,
  });

  // Update latest pointer
  await env.PROPERTY_UPDATES.put(LATEST_KEY, digest.date);

  // Update the history index (keep last 90 dates)
  const indexRaw = await env.PROPERTY_UPDATES.get(HISTORY_INDEX_KEY);
  const index: string[] = indexRaw ? JSON.parse(indexRaw) : [];
  if (!index.includes(digest.date)) {
    index.unshift(digest.date);
  }
  const trimmed = index.slice(0, 90);
  await env.PROPERTY_UPDATES.put(HISTORY_INDEX_KEY, JSON.stringify(trimmed));
}

/**
 * Retrieves the latest daily digest.
 */
export async function getLatestDigest(env: Env): Promise<DailyDigest | null> {
  const latestDate = await env.PROPERTY_UPDATES.get(LATEST_KEY);
  if (!latestDate) return null;
  return getDigestByDate(env, latestDate);
}

/**
 * Retrieves a digest for a specific date.
 */
export async function getDigestByDate(env: Env, date: string): Promise<DailyDigest | null> {
  const key = `${DIGEST_PREFIX}${date}`;
  const raw = await env.PROPERTY_UPDATES.get(key);
  if (!raw) return null;
  return JSON.parse(raw) as DailyDigest;
}

/**
 * Lists available digest dates.
 */
export async function listDigestDates(env: Env): Promise<string[]> {
  const raw = await env.PROPERTY_UPDATES.get(HISTORY_INDEX_KEY);
  return raw ? JSON.parse(raw) : [];
}

/**
 * Checks if an update ID has been seen before (for deduplication across days).
 * Stores seen IDs with a 7-day TTL to only surface genuinely new content.
 */
export async function isUpdateNew(env: Env, updateId: string): Promise<boolean> {
  const key = `seen:${updateId}`;
  const existing = await env.PROPERTY_UPDATES.get(key);
  return existing === null;
}

/**
 * Marks an update as seen.
 */
export async function markUpdateSeen(env: Env, updateId: string): Promise<void> {
  const key = `seen:${updateId}`;
  await env.PROPERTY_UPDATES.put(key, '1', {
    expirationTtl: 7 * 24 * 60 * 60,
  });
}

/**
 * Filters a list of updates to only include ones not seen in the past 7 days.
 */
export async function filterNewUpdates(
  env: Env,
  updates: PropertyUpdate[]
): Promise<PropertyUpdate[]> {
  const results: PropertyUpdate[] = [];
  for (const update of updates) {
    if (await isUpdateNew(env, update.id)) {
      results.push(update);
      await markUpdateSeen(env, update.id);
    }
  }
  return results;
}
