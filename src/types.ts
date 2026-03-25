export interface Env {
  PROPERTY_UPDATES: KVNamespace;
}

export type AustralianState = 'NSW' | 'VIC' | 'QLD' | 'SA' | 'WA' | 'TAS' | 'NT' | 'ACT';

export interface LawSource {
  state: AustralianState;
  name: string;
  url: string;
  type: 'legislation' | 'gazette' | 'policy' | 'grants';
}

export interface PropertyUpdate {
  id: string;
  state: AustralianState;
  title: string;
  summary: string;
  url: string;
  source: string;
  category: UpdateCategory;
  dateFound: string;
  relevanceScore: number;
}

export type UpdateCategory =
  | 'first-home-buyer-grant'
  | 'stamp-duty'
  | 'planning-zoning'
  | 'tenancy-law'
  | 'foreign-investment'
  | 'tax-policy'
  | 'housing-affordability'
  | 'building-regulation'
  | 'general-property-law';

export interface DailyDigest {
  date: string;
  updates: PropertyUpdate[];
  statesScraped: AustralianState[];
  errors: ScrapeError[];
}

export interface ScrapeError {
  state: AustralianState;
  source: string;
  error: string;
}
