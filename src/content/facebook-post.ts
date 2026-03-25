import { DailyDigest, PropertyUpdate } from '../types';
import { ContentConfig, FacebookPostContent } from './types';

const CATEGORY_LABELS: Record<string, string> = {
  'first-home-buyer-grant': 'First Home Buyer Grant',
  'stamp-duty': 'Stamp Duty',
  'planning-zoning': 'Planning & Zoning',
  'tenancy-law': 'Tenancy Law',
  'foreign-investment': 'Foreign Investment',
  'tax-policy': 'Tax Policy',
  'housing-affordability': 'Housing Affordability',
  'building-regulation': 'Building Regulation',
  'general-property-law': 'Property Law',
};

/**
 * Generates Facebook post content optimized for organic reach:
 *
 * CRO principles:
 * - 40-80 word sweet spot for organic reach
 * - Lead with a question or relatable statement (stops the scroll)
 * - Use line breaks for readability (not walls of text)
 * - Include value upfront before the "See more" fold (~125 chars)
 * - End with engagement prompt (question to drive comments)
 * - Link in post body (Facebook deprioritizes link-only posts less in 2025+)
 * - Suggest image description for companion visual
 */
export function generateFacebookPost(
  digest: DailyDigest,
  config: ContentConfig
): FacebookPostContent {
  const count = digest.updates.length;
  const topUpdate = digest.updates[0];
  const topCategory = topUpdate?.category || 'general-property-law';
  const states = [...new Set(digest.updates.map((u) => u.state))];

  const body = buildBody(digest, count, topUpdate, topCategory, states, config);
  const link = `${config.siteUrl}/updates/${digest.date}`;
  const imageDescription = buildImageDescription(digest, count, states);

  return { body, link, imageDescription };
}

function buildBody(
  digest: DailyDigest,
  count: number,
  topUpdate: PropertyUpdate | undefined,
  topCategory: string,
  states: string[],
  config: ContentConfig
): string {
  const day = new Date(digest.date).getDate();

  // Rotating opening hooks (relatable questions that stop the scroll)
  const openers = [
    'Dreaming of owning your first home? 🏠',
    'Still renting? Here\'s what changed in property law today.',
    'If you\'re saving for a home deposit, you need to see this.',
    'Property law just changed — and it could affect your home buying plans.',
    `${count} property law updates dropped today. Here's what matters for first home buyers.`,
  ];

  const opener = openers[day % openers.length];

  // Build the update summary (2-3 top items)
  const highlights = digest.updates.slice(0, 3);
  const bulletPoints = highlights
    .map((u) => `✅ ${u.state}: ${u.title.substring(0, 80)}${u.title.length > 80 ? '...' : ''}`)
    .join('\n');

  // States covered
  const stateStr = states.length > 3
    ? `${states.slice(0, 3).join(', ')} + ${states.length - 3} more`
    : states.join(', ');

  const body = [
    opener,
    '',
    `📋 Today's ${count} updates cover: ${stateStr}`,
    '',
    bulletPoints,
    '',
    `👉 Full free digest: ${config.siteUrl}/updates/${digest.date}`,
    '',
    '💬 Which state are you looking to buy in? Drop it in the comments — we\'ll highlight the updates that matter most to you.',
  ].join('\n');

  return body;
}

function buildImageDescription(
  digest: DailyDigest,
  count: number,
  states: string[]
): string {
  return `Infographic showing ${count} Australian property law updates across ${states.length} states (${states.join(', ')}). Blue gradient background with white text. Top headline: "${count} Property Law Updates for First Home Buyers". Shows a map of Australia with state badges. Brand: ${digest.date} daily digest.`;
}
