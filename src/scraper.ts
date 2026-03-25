import { LawSource, PropertyUpdate, ScrapeError, AustralianState } from './types';
import { analyzeRelevance } from './relevance';

/**
 * Scrapes a single source URL and extracts text content.
 * Uses lightweight HTML parsing suitable for Cloudflare Workers.
 */
async function fetchPageContent(source: LawSource): Promise<string> {
  const response = await fetch(source.url, {
    headers: {
      'User-Agent': 'AU-Property-Law-Monitor/1.0 (Automated policy tracker)',
      Accept: 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
      'Accept-Language': 'en-AU,en;q=0.9',
    },
    cf: {
      cacheTtl: 3600,
      cacheEverything: false,
    },
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  return await response.text();
}

/**
 * Extracts meaningful text blocks from raw HTML.
 * Strips tags and returns text segments that could contain policy updates.
 */
function extractTextBlocks(html: string): string[] {
  // Remove script and style content
  let cleaned = html.replace(/<script[\s\S]*?<\/script>/gi, '');
  cleaned = cleaned.replace(/<style[\s\S]*?<\/style>/gi, '');
  cleaned = cleaned.replace(/<nav[\s\S]*?<\/nav>/gi, '');
  cleaned = cleaned.replace(/<footer[\s\S]*?<\/footer>/gi, '');
  cleaned = cleaned.replace(/<header[\s\S]*?<\/header>/gi, '');

  // Extract content from headings, paragraphs, list items, and links
  const patterns = [
    /<h[1-6][^>]*>([\s\S]*?)<\/h[1-6]>/gi,
    /<p[^>]*>([\s\S]*?)<\/p>/gi,
    /<li[^>]*>([\s\S]*?)<\/li>/gi,
    /<a[^>]*>([\s\S]*?)<\/a>/gi,
    /<td[^>]*>([\s\S]*?)<\/td>/gi,
    /<div[^>]*class="[^"]*(?:title|summary|description|content|article|result)[^"]*"[^>]*>([\s\S]*?)<\/div>/gi,
  ];

  const blocks: string[] = [];
  for (const pattern of patterns) {
    let match;
    while ((match = pattern.exec(cleaned)) !== null) {
      const text = match[1]
        .replace(/<[^>]+>/g, ' ')
        .replace(/&nbsp;/g, ' ')
        .replace(/&amp;/g, '&')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&#\d+;/g, '')
        .replace(/\s+/g, ' ')
        .trim();
      if (text.length > 15 && text.length < 2000) {
        blocks.push(text);
      }
    }
  }

  return [...new Set(blocks)];
}

/**
 * Extracts links from HTML that might point to specific legislation or policy pages.
 */
function extractLinks(html: string, baseUrl: string): { text: string; href: string }[] {
  const linkPattern = /<a[^>]*href="([^"]*)"[^>]*>([\s\S]*?)<\/a>/gi;
  const links: { text: string; href: string }[] = [];
  let match;

  while ((match = linkPattern.exec(html)) !== null) {
    const href = match[1];
    const text = match[2].replace(/<[^>]+>/g, '').trim();
    if (text.length > 5 && href && !href.startsWith('#') && !href.startsWith('javascript:')) {
      let fullUrl = href;
      if (href.startsWith('/')) {
        const url = new URL(baseUrl);
        fullUrl = `${url.origin}${href}`;
      } else if (!href.startsWith('http')) {
        fullUrl = `${baseUrl.replace(/\/$/, '')}/${href}`;
      }
      links.push({ text, href: fullUrl });
    }
  }

  return links;
}

/**
 * Generates a deterministic ID for deduplication.
 */
function generateId(state: AustralianState, title: string, source: string): string {
  const input = `${state}-${title}-${source}`.toLowerCase().replace(/\s+/g, '-').slice(0, 100);
  let hash = 0;
  for (let i = 0; i < input.length; i++) {
    const char = input.charCodeAt(i);
    hash = ((hash << 5) - hash + char) | 0;
  }
  return `${state.toLowerCase()}-${Math.abs(hash).toString(36)}`;
}

/**
 * Scrapes a single source and returns relevant property updates.
 */
export async function scrapeSource(source: LawSource): Promise<{
  updates: PropertyUpdate[];
  error?: ScrapeError;
}> {
  try {
    const html = await fetchPageContent(source);
    const textBlocks = extractTextBlocks(html);
    const links = extractLinks(html, source.url);
    const updates: PropertyUpdate[] = [];
    const today = new Date().toISOString().split('T')[0];

    // Analyze text blocks for relevance
    for (const block of textBlocks) {
      const relevance = analyzeRelevance(block);
      if (relevance.isRelevant) {
        const title = block.length > 120 ? block.slice(0, 117) + '...' : block;
        updates.push({
          id: generateId(source.state, title, source.name),
          state: source.state,
          title,
          summary: `Found in ${source.name}: ${relevance.matchedKeywords.join(', ')}`,
          url: source.url,
          source: source.name,
          category: relevance.category,
          dateFound: today,
          relevanceScore: relevance.score,
        });
      }
    }

    // Analyze links for relevance (link text often contains update titles)
    for (const link of links) {
      const relevance = analyzeRelevance(link.text);
      if (relevance.isRelevant) {
        updates.push({
          id: generateId(source.state, link.text, source.name),
          state: source.state,
          title: link.text,
          summary: `Link found in ${source.name}: ${relevance.matchedKeywords.join(', ')}`,
          url: link.href,
          source: source.name,
          category: relevance.category,
          dateFound: today,
          relevanceScore: relevance.score,
        });
      }
    }

    // Deduplicate by ID
    const seen = new Set<string>();
    const deduped = updates.filter((u) => {
      if (seen.has(u.id)) return false;
      seen.add(u.id);
      return true;
    });

    // Sort by relevance score descending
    deduped.sort((a, b) => b.relevanceScore - a.relevanceScore);

    return { updates: deduped.slice(0, 25) };
  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : String(err);
    return {
      updates: [],
      error: {
        state: source.state,
        source: source.name,
        error: errorMessage,
      },
    };
  }
}
