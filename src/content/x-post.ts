import { DailyDigest, PropertyUpdate } from '../types';
import { ContentConfig, XPostContent } from './types';

const CATEGORY_HOOKS: Record<string, string[]> = {
  'first-home-buyer-grant': [
    'First home buyer alert',
    'New grant update just dropped',
    'Aspiring homeowners, read this',
  ],
  'stamp-duty': [
    'Stamp duty change alert',
    'This could save you thousands on stamp duty',
    'New stamp duty update',
  ],
  'housing-affordability': [
    'Housing affordability update',
    'New housing policy just announced',
    'This changes the game for renters',
  ],
  'tax-policy': [
    'Property tax update',
    'New tax policy affecting home buyers',
    'Tax change alert for buyers',
  ],
  'tenancy-law': [
    'Renters, this affects you',
    'Tenancy law change',
    'New rental law update',
  ],
};

const DEFAULT_HOOKS = [
  'Property law update',
  'New update for AU home buyers',
  'Renter to owner alert',
];

const HASHTAGS = [
  '#FirstHomeBuyer',
  '#AustralianProperty',
  '#RenterToOwner',
  '#PropertyLaw',
  '#FHOG',
  '#HomeOwnership',
  '#AusProperty',
  '#StampDuty',
];

/**
 * Generates X (Twitter) post content optimized for engagement:
 * - Main post: hook + key stat + CTA (under 280 chars)
 * - Thread: top 3 updates as individual tweets for depth
 * - Hashtags: 2-3 relevant tags (more hurts engagement)
 *
 * CRO principles applied:
 * - Front-load the hook (first 50 chars visible in timeline)
 * - Use numbers for scannability
 * - End with engagement trigger (question or CTA)
 * - Thread for depth without cluttering main post
 */
export function generateXPost(digest: DailyDigest, config: ContentConfig): XPostContent {
  const count = digest.updates.length;
  const topUpdate = digest.updates[0];
  const topCategory = topUpdate?.category || 'general-property-law';
  const topState = topUpdate?.state || 'AU';

  // Select hook based on top category
  const hooks = CATEGORY_HOOKS[topCategory] || DEFAULT_HOOKS;
  const day = new Date(digest.date).getDate();
  const hook = hooks[day % hooks.length];

  // Select 2-3 relevant hashtags
  const selectedTags = selectHashtags(digest, 3);

  // Main post: hook + stat + CTA (keep under 280)
  const mainPost = buildMainPost(hook, count, topState, topUpdate, config, selectedTags);

  // Thread: expand on top updates
  const thread = buildThread(digest, config);

  return {
    mainPost,
    thread,
    hashtags: selectedTags,
  };
}

function buildMainPost(
  hook: string,
  count: number,
  state: string,
  topUpdate: PropertyUpdate | undefined,
  config: ContentConfig,
  hashtags: string[]
): string {
  const tagStr = hashtags.slice(0, 2).join(' ');

  // Template: "🏠 [Hook]\n\n[count] new property law updates in AU today.\n\nTop: [title snippet]\n\n[CTA]\n\n[hashtags]"
  const parts = [
    `🏠 ${hook}`,
    '',
    `${count} new AU property law updates today affecting first home buyers.`,
  ];

  if (topUpdate) {
    const titleSnippet = topUpdate.title.substring(0, 60);
    parts.push('');
    parts.push(`📌 ${titleSnippet}${topUpdate.title.length > 60 ? '...' : ''}`);
  }

  parts.push('');
  parts.push(`Full digest 👇`);
  parts.push('');
  parts.push(tagStr);

  let post = parts.join('\n');

  // Ensure under 280 chars
  if (post.length > 280) {
    post = [
      `🏠 ${hook}`,
      '',
      `${count} new AU property law updates for first home buyers.`,
      '',
      `Full digest 👇`,
      '',
      tagStr,
    ].join('\n');
  }

  if (post.length > 280) {
    post = `🏠 ${count} new AU property law updates for first home buyers today.\n\nFull digest 👇\n\n${tagStr}`;
  }

  return post;
}

function buildThread(digest: DailyDigest, config: ContentConfig): string[] {
  const thread: string[] = [];
  const topUpdates = digest.updates.slice(0, 4);

  for (let i = 0; i < topUpdates.length; i++) {
    const u = topUpdates[i];
    const num = i + 1;
    const titleSnippet = u.title.substring(0, 80);
    const summarySnippet = u.summary.substring(0, 100);

    let tweet = `${num}/${topUpdates.length} ${getStateEmoji(u.state)} ${u.state}\n\n${titleSnippet}\n\n${summarySnippet}${u.summary.length > 100 ? '...' : ''}\n\n🔗 ${u.url}`;

    if (tweet.length > 280) {
      tweet = `${num}/${topUpdates.length} ${getStateEmoji(u.state)} ${u.state}\n\n${titleSnippet}${u.title.length > 80 ? '...' : ''}\n\n🔗 ${u.url}`;
    }

    thread.push(tweet);
  }

  // Final thread tweet: engagement CTA
  thread.push(
    `Are you a renter planning to buy your first home?\n\nWe track property law changes across all 8 AU states daily so you don't miss savings.\n\nFollow ${config.xHandle} for daily updates 🏠`
  );

  return thread;
}

function selectHashtags(digest: DailyDigest, count: number): string[] {
  const selected: string[] = ['#FirstHomeBuyer', '#AusProperty'];

  const categories = new Set(digest.updates.map((u) => u.category));
  if (categories.has('stamp-duty')) selected.push('#StampDuty');
  else if (categories.has('first-home-buyer-grant')) selected.push('#FHOG');
  else if (categories.has('housing-affordability')) selected.push('#HousingCrisis');
  else selected.push('#PropertyLaw');

  return selected.slice(0, count);
}

function getStateEmoji(state: string): string {
  const map: Record<string, string> = {
    NSW: '🔵',
    VIC: '🔷',
    QLD: '🟡',
    SA: '🔴',
    WA: '⚫',
    TAS: '🟢',
    NT: '🟠',
    ACT: '🟣',
  };
  return map[state] || '🏠';
}
