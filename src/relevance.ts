import { UpdateCategory } from './types';

/**
 * Keywords and patterns used to determine if scraped content is relevant
 * to first home buyers and real estate policy in Australia.
 */

interface KeywordGroup {
  category: UpdateCategory;
  weight: number;
  keywords: string[];
}

const KEYWORD_GROUPS: KeywordGroup[] = [
  {
    category: 'first-home-buyer-grant',
    weight: 10,
    keywords: [
      'first home',
      'first home buyer',
      'first home owner',
      'fhog',
      'first home owner grant',
      'first home buyer grant',
      'first home guarantee',
      'home buyer fund',
      'home buyer assistance',
      'new home grant',
      'first home concession',
      'home buyer concession',
    ],
  },
  {
    category: 'stamp-duty',
    weight: 9,
    keywords: [
      'stamp duty',
      'transfer duty',
      'land transfer duty',
      'duty concession',
      'duty exemption',
      'conveyance duty',
      'stamp duty reform',
      'duty threshold',
      'property tax reform',
      'land tax threshold',
    ],
  },
  {
    category: 'housing-affordability',
    weight: 8,
    keywords: [
      'housing affordability',
      'affordable housing',
      'social housing',
      'housing supply',
      'housing crisis',
      'housing strategy',
      'housing policy',
      'housing fund',
      'shared equity',
      'help to buy',
      'rent to buy',
      'rent to own',
      'housing target',
      'housing accord',
      'national housing',
    ],
  },
  {
    category: 'planning-zoning',
    weight: 6,
    keywords: [
      'planning reform',
      'zoning change',
      'rezoning',
      'medium density',
      'high density',
      'residential development',
      'subdivision',
      'development application',
      'planning scheme amendment',
      'urban infill',
      'greenfield',
      'missing middle',
      'planning code',
    ],
  },
  {
    category: 'tax-policy',
    weight: 7,
    keywords: [
      'land tax',
      'property tax',
      'capital gains',
      'negative gearing',
      'investment property tax',
      'foreign buyer surcharge',
      'absentee owner',
      'vacancy tax',
      'land value',
      'property valuation',
    ],
  },
  {
    category: 'tenancy-law',
    weight: 5,
    keywords: [
      'residential tenancy',
      'tenancy act',
      'rental reform',
      'rental law',
      'tenant rights',
      'rent increase',
      'rent cap',
      'bond',
      'eviction',
      'lease reform',
      'renter rights',
      'rental market',
    ],
  },
  {
    category: 'foreign-investment',
    weight: 6,
    keywords: [
      'foreign investment',
      'foreign buyer',
      'foreign purchaser',
      'firb',
      'foreign ownership',
      'non-resident',
      'overseas buyer',
    ],
  },
  {
    category: 'building-regulation',
    weight: 4,
    keywords: [
      'building code',
      'building standard',
      'building regulation',
      'construction code',
      'national construction code',
      'building defect',
      'building compliance',
      'building approval',
    ],
  },
  {
    category: 'general-property-law',
    weight: 3,
    keywords: [
      'property law',
      'real property',
      'conveyancing',
      'torrens title',
      'strata',
      'body corporate',
      'owners corporation',
      'settlement',
      'property transfer',
      'land title',
      'real estate regulation',
      'property agent',
      'estate agent',
    ],
  },
];

export interface RelevanceResult {
  isRelevant: boolean;
  score: number;
  category: UpdateCategory;
  matchedKeywords: string[];
}

/**
 * Analyzes text content for relevance to first home buyers and property policy.
 * Returns a relevance score and the best-matching category.
 */
export function analyzeRelevance(text: string): RelevanceResult {
  const lowerText = text.toLowerCase();
  let bestCategory: UpdateCategory = 'general-property-law';
  let bestWeight = 0;
  let totalScore = 0;
  const allMatched: string[] = [];

  for (const group of KEYWORD_GROUPS) {
    const matched = group.keywords.filter((kw) => lowerText.includes(kw));
    if (matched.length > 0) {
      const groupScore = matched.length * group.weight;
      totalScore += groupScore;
      allMatched.push(...matched);
      if (group.weight > bestWeight) {
        bestWeight = group.weight;
        bestCategory = group.category;
      }
    }
  }

  return {
    isRelevant: totalScore >= 5,
    score: totalScore,
    category: bestCategory,
    matchedKeywords: [...new Set(allMatched)],
  };
}
