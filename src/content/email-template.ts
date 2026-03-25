import { DailyDigest, PropertyUpdate } from '../types';
import { ContentConfig, EmailContent } from './types';

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

const CATEGORY_EMOJI: Record<string, string> = {
  'first-home-buyer-grant': '🏠',
  'stamp-duty': '📋',
  'planning-zoning': '🏗️',
  'tenancy-law': '📜',
  'foreign-investment': '🌏',
  'tax-policy': '💰',
  'housing-affordability': '🔑',
  'building-regulation': '🔨',
  'general-property-law': '⚖️',
};

/**
 * Subject line formulas using CRO best practices:
 * - Curiosity gap + specificity
 * - Numbers for scannability
 * - Urgency without spam triggers
 * - Personalization via state when available
 */
function generateSubjectLine(digest: DailyDigest): string {
  const count = digest.updates.length;
  const topCategory = getTopCategory(digest.updates);
  const topState = getTopState(digest.updates);

  const templates = [
    `${count} Property Law Changes Affecting First Home Buyers Today`,
    `New ${CATEGORY_LABELS[topCategory] || 'Property'} Updates: What Renters Need to Know`,
    `${topState} Property Alert: ${count} Updates That Could Save You Thousands`,
    `Your Weekly Path to Ownership: ${count} New Law Changes`,
    `Breaking: ${CATEGORY_LABELS[topCategory] || 'Property Law'} Changes in ${topState}`,
  ];

  // Rotate based on day of month for variety
  const day = new Date(digest.date).getDate();
  return templates[day % templates.length];
}

function generatePreheader(digest: DailyDigest): string {
  const topUpdate = digest.updates[0];
  if (!topUpdate) return 'Stay informed on your path from renter to owner.';
  return `Top update: ${topUpdate.title.substring(0, 80)}...`;
}

function getTopCategory(updates: PropertyUpdate[]): string {
  const counts: Record<string, number> = {};
  for (const u of updates) {
    counts[u.category] = (counts[u.category] || 0) + 1;
  }
  return Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0] || 'general-property-law';
}

function getTopState(updates: PropertyUpdate[]): string {
  const counts: Record<string, number> = {};
  for (const u of updates) {
    counts[u.state] = (counts[u.state] || 0) + 1;
  }
  return Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0] || 'AU';
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-AU', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

function groupUpdatesByCategory(updates: PropertyUpdate[]): Record<string, PropertyUpdate[]> {
  const grouped: Record<string, PropertyUpdate[]> = {};
  for (const u of updates) {
    if (!grouped[u.category]) grouped[u.category] = [];
    grouped[u.category].push(u);
  }
  return grouped;
}

function renderUpdateCard(update: PropertyUpdate): string {
  const emoji = CATEGORY_EMOJI[update.category] || '📰';
  const label = CATEGORY_LABELS[update.category] || 'Update';
  return `
    <tr>
      <td style="padding: 16px 24px;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background: #ffffff; border-radius: 8px; border: 1px solid #e5e7eb;">
          <tr>
            <td style="padding: 20px;">
              <p style="margin: 0 0 4px; font-size: 12px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;">
                ${emoji} ${label} · ${update.state}
              </p>
              <h3 style="margin: 0 0 8px; font-size: 18px; color: #111827; line-height: 1.3;">
                <a href="${update.url}" style="color: #111827; text-decoration: none;">${escapeHtml(update.title)}</a>
              </h3>
              <p style="margin: 0 0 12px; font-size: 14px; color: #4b5563; line-height: 1.5;">
                ${escapeHtml(update.summary.substring(0, 200))}${update.summary.length > 200 ? '...' : ''}
              </p>
              <a href="${update.url}" style="display: inline-block; padding: 8px 16px; background: #2563eb; color: #ffffff; text-decoration: none; border-radius: 6px; font-size: 14px; font-weight: 600;">
                Read Full Update →
              </a>
            </td>
          </tr>
        </table>
      </td>
    </tr>`;
}

function renderStateSummary(digest: DailyDigest): string {
  const byState: Record<string, number> = {};
  for (const u of digest.updates) {
    byState[u.state] = (byState[u.state] || 0) + 1;
  }
  const states = Object.entries(byState)
    .sort((a, b) => b[1] - a[1])
    .map(([state, count]) => `<span style="display: inline-block; padding: 4px 12px; margin: 2px 4px; background: #eff6ff; color: #1d4ed8; border-radius: 16px; font-size: 13px; font-weight: 500;">${state}: ${count}</span>`)
    .join(' ');
  return states;
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/**
 * Generates a CRO-optimized email using inverted pyramid layout:
 * 1. Hero banner with key stat (above the fold)
 * 2. Top 3 updates with CTA buttons (primary content)
 * 3. Full categorized list (secondary content)
 * 4. Social proof + share CTA (conversion)
 * 5. Footer with unsubscribe (compliance)
 *
 * Mobile-first: single column, 600px max, large tap targets (44px+)
 */
export function generateEmail(digest: DailyDigest, config: ContentConfig): EmailContent {
  const subject = generateSubjectLine(digest);
  const preheader = generatePreheader(digest);
  const topUpdates = digest.updates.slice(0, 3);
  const remainingUpdates = digest.updates.slice(3, 10);
  const dateFormatted = formatDate(digest.date);

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${escapeHtml(subject)}</title>
  <!--[if mso]><style>table{border-collapse:collapse;}</style><![endif]-->
</head>
<body style="margin: 0; padding: 0; background: #f3f4f6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
  <!-- Preheader text (hidden) -->
  <div style="display: none; max-height: 0; overflow: hidden;">
    ${escapeHtml(preheader)}&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;
  </div>

  <table width="100%" cellpadding="0" cellspacing="0" style="background: #f3f4f6;">
    <tr>
      <td align="center" style="padding: 20px 8px;">
        <table width="600" cellpadding="0" cellspacing="0" style="max-width: 600px; width: 100%; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">

          <!-- SECTION 1: Hero Banner (Above the Fold) -->
          <tr>
            <td style="background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); padding: 32px 24px; text-align: center;">
              <h1 style="margin: 0 0 8px; color: #ffffff; font-size: 24px; font-weight: 700; line-height: 1.2;">
                ${escapeHtml(config.brandName)}
              </h1>
              <p style="margin: 0 0 16px; color: #bfdbfe; font-size: 14px;">
                ${dateFormatted}
              </p>
              <div style="background: rgba(255,255,255,0.15); border-radius: 8px; padding: 16px; display: inline-block;">
                <p style="margin: 0; color: #ffffff; font-size: 36px; font-weight: 800; line-height: 1;">
                  ${digest.updates.length}
                </p>
                <p style="margin: 4px 0 0; color: #bfdbfe; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">
                  New Updates Today
                </p>
              </div>
            </td>
          </tr>

          <!-- State badges -->
          <tr>
            <td style="padding: 16px 24px; text-align: center; border-bottom: 1px solid #e5e7eb;">
              ${renderStateSummary(digest)}
            </td>
          </tr>

          <!-- SECTION 2: Top Updates (Primary CTA Zone) -->
          <tr>
            <td style="padding: 24px 24px 8px;">
              <h2 style="margin: 0; font-size: 20px; color: #111827;">
                🔥 Top Updates
              </h2>
              <p style="margin: 4px 0 0; font-size: 14px; color: #6b7280;">
                The most important changes for aspiring homeowners
              </p>
            </td>
          </tr>
          ${topUpdates.map(renderUpdateCard).join('')}

          <!-- SECTION 3: More Updates -->
          ${remainingUpdates.length > 0 ? `
          <tr>
            <td style="padding: 24px 24px 8px;">
              <h2 style="margin: 0; font-size: 18px; color: #111827;">
                📋 More Updates
              </h2>
            </td>
          </tr>
          <tr>
            <td style="padding: 0 24px 16px;">
              <table width="100%" cellpadding="0" cellspacing="0">
                ${remainingUpdates.map((u) => `
                <tr>
                  <td style="padding: 12px 0; border-bottom: 1px solid #f3f4f6;">
                    <p style="margin: 0 0 2px; font-size: 12px; color: #6b7280;">
                      ${CATEGORY_EMOJI[u.category] || '📰'} ${u.state} · ${CATEGORY_LABELS[u.category] || 'Update'}
                    </p>
                    <a href="${u.url}" style="color: #2563eb; text-decoration: none; font-size: 15px; font-weight: 500; line-height: 1.3;">
                      ${escapeHtml(u.title)}
                    </a>
                  </td>
                </tr>`).join('')}
              </table>
            </td>
          </tr>` : ''}

          <!-- SECTION 4: CTA - View All -->
          <tr>
            <td style="padding: 16px 24px 24px; text-align: center;">
              <a href="${config.siteUrl}/updates/${digest.date}" style="display: inline-block; padding: 14px 32px; background: #16a34a; color: #ffffff; text-decoration: none; border-radius: 8px; font-size: 16px; font-weight: 700;">
                View All ${digest.updates.length} Updates →
              </a>
            </td>
          </tr>

          <!-- SECTION 5: Social Proof + Share -->
          <tr>
            <td style="background: #f9fafb; padding: 24px; text-align: center; border-top: 1px solid #e5e7eb;">
              <p style="margin: 0 0 12px; font-size: 14px; color: #4b5563;">
                Know someone saving for their first home? Share this digest.
              </p>
              <a href="https://twitter.com/intent/tweet?text=Check%20out%20today%27s%20AU%20property%20law%20updates%20for%20first%20home%20buyers&url=${encodeURIComponent(config.siteUrl)}" style="display: inline-block; padding: 8px 16px; margin: 0 4px; background: #000000; color: #ffffff; text-decoration: none; border-radius: 6px; font-size: 13px;">Share on X</a>
              <a href="https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(config.siteUrl)}" style="display: inline-block; padding: 8px 16px; margin: 0 4px; background: #1877f2; color: #ffffff; text-decoration: none; border-radius: 6px; font-size: 13px;">Share on Facebook</a>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding: 20px 24px; text-align: center; border-top: 1px solid #e5e7eb;">
              <p style="margin: 0 0 8px; font-size: 12px; color: #9ca3af;">
                ${escapeHtml(config.brandName)} · Australian Property Law Updates for First Home Buyers
              </p>
              <p style="margin: 0; font-size: 12px; color: #9ca3af;">
                <a href="${config.unsubscribeUrl}" style="color: #9ca3af;">Unsubscribe</a> · <a href="${config.siteUrl}/preferences" style="color: #9ca3af;">Update Preferences</a>
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>`;

  const plainText = generatePlainText(digest, config);

  return { subject, preheader, html, plainText };
}

function generatePlainText(digest: DailyDigest, config: ContentConfig): string {
  const lines: string[] = [
    `${config.brandName} - Daily Property Law Digest`,
    `${formatDate(digest.date)}`,
    `${'='.repeat(50)}`,
    '',
    `${digest.updates.length} new updates found today.`,
    '',
    'TOP UPDATES',
    '-'.repeat(30),
  ];

  for (const u of digest.updates.slice(0, 10)) {
    lines.push('');
    lines.push(`[${u.state}] ${CATEGORY_LABELS[u.category] || u.category}`);
    lines.push(u.title);
    lines.push(u.summary.substring(0, 150));
    lines.push(`Read more: ${u.url}`);
  }

  lines.push('');
  lines.push('-'.repeat(30));
  lines.push(`View all updates: ${config.siteUrl}/updates/${digest.date}`);
  lines.push('');
  lines.push(`Unsubscribe: ${config.unsubscribeUrl}`);

  return lines.join('\n');
}
