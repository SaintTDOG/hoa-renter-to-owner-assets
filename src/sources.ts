import { LawSource } from './types';

/**
 * Australian government legislation, gazette, and policy sources by state.
 * These are official government websites that publish property law updates,
 * first home buyer grants, stamp duty changes, and housing policy.
 */
export const SOURCES: LawSource[] = [
  // === NEW SOUTH WALES ===
  {
    state: 'NSW',
    name: 'NSW Legislation - Property',
    url: 'https://legislation.nsw.gov.au/search?query=property+conveyancing&status=inforce&sort=date',
    type: 'legislation',
  },
  {
    state: 'NSW',
    name: 'Revenue NSW - First Home Buyer',
    url: 'https://www.revenue.nsw.gov.au/grants-schemes/first-home-buyer',
    type: 'grants',
  },
  {
    state: 'NSW',
    name: 'NSW Government Gazette',
    url: 'https://gazette.legislation.nsw.gov.au/so/download.w3p?id=Gazette_Listing',
    type: 'gazette',
  },
  {
    state: 'NSW',
    name: 'NSW Planning Portal',
    url: 'https://www.planning.nsw.gov.au/policy-and-legislation/housing',
    type: 'policy',
  },

  // === VICTORIA ===
  {
    state: 'VIC',
    name: 'Victorian Legislation - Property',
    url: 'https://www.legislation.vic.gov.au/search?query=property+real+estate&category=Act&sort=relevance',
    type: 'legislation',
  },
  {
    state: 'VIC',
    name: 'SRO Victoria - First Home Owner',
    url: 'https://www.sro.vic.gov.au/first-home-owner',
    type: 'grants',
  },
  {
    state: 'VIC',
    name: 'Victoria Government Gazette',
    url: 'https://www.gazette.vic.gov.au/',
    type: 'gazette',
  },
  {
    state: 'VIC',
    name: 'DFFH Victoria - Housing',
    url: 'https://www.homes.vic.gov.au/housing-policy',
    type: 'policy',
  },

  // === QUEENSLAND ===
  {
    state: 'QLD',
    name: 'Queensland Legislation - Property',
    url: 'https://www.legislation.qld.gov.au/search?query=property+law&status=inforce&sort=date',
    type: 'legislation',
  },
  {
    state: 'QLD',
    name: 'QLD Treasury - First Home Grant',
    url: 'https://www.qld.gov.au/housing/buying-owning-home/financial-help-702702702702702702702702702702702/first-home-owners-grant',
    type: 'grants',
  },
  {
    state: 'QLD',
    name: 'QLD Government Gazette',
    url: 'https://www.publications.qld.gov.au/dataset/queensland-government-gazette',
    type: 'gazette',
  },
  {
    state: 'QLD',
    name: 'QLD Housing Policy',
    url: 'https://www.qld.gov.au/housing/buying-owning-home',
    type: 'policy',
  },

  // === SOUTH AUSTRALIA ===
  {
    state: 'SA',
    name: 'SA Legislation - Property',
    url: 'https://www.legislation.sa.gov.au/legislation/property',
    type: 'legislation',
  },
  {
    state: 'SA',
    name: 'RevenueSA - First Home Owner Grant',
    url: 'https://www.revenuesa.sa.gov.au/grants-and-concessions/first-home-owners',
    type: 'grants',
  },
  {
    state: 'SA',
    name: 'SA Government Gazette',
    url: 'https://www.governmentgazette.sa.gov.au/',
    type: 'gazette',
  },
  {
    state: 'SA',
    name: 'SA Housing Authority',
    url: 'https://www.housing.sa.gov.au/',
    type: 'policy',
  },

  // === WESTERN AUSTRALIA ===
  {
    state: 'WA',
    name: 'WA Legislation - Property',
    url: 'https://www.legislation.wa.gov.au/legislation/statutes.nsf/default.html',
    type: 'legislation',
  },
  {
    state: 'WA',
    name: 'WA First Home Owner Grant',
    url: 'https://www.wa.gov.au/service/community-services/grants-and-subsidies/apply-first-home-owner-grant',
    type: 'grants',
  },
  {
    state: 'WA',
    name: 'WA Government Gazette',
    url: 'https://www.legislation.wa.gov.au/legislation/gazettes.nsf/',
    type: 'gazette',
  },
  {
    state: 'WA',
    name: 'WA Housing - Keystart',
    url: 'https://www.keystart.com.au/government-programs',
    type: 'policy',
  },

  // === TASMANIA ===
  {
    state: 'TAS',
    name: 'Tasmanian Legislation - Property',
    url: 'https://www.legislation.tas.gov.au/',
    type: 'legislation',
  },
  {
    state: 'TAS',
    name: 'SRO Tasmania - First Home Owner',
    url: 'https://www.sro.tas.gov.au/first-home-owner',
    type: 'grants',
  },
  {
    state: 'TAS',
    name: 'Tasmania Government Gazette',
    url: 'https://www.gazette.tas.gov.au/',
    type: 'gazette',
  },
  {
    state: 'TAS',
    name: 'TAS Housing Policy',
    url: 'https://www.communities.tas.gov.au/housing',
    type: 'policy',
  },

  // === NORTHERN TERRITORY ===
  {
    state: 'NT',
    name: 'NT Legislation - Property',
    url: 'https://legislation.nt.gov.au/',
    type: 'legislation',
  },
  {
    state: 'NT',
    name: 'NT Treasury - HomeBuild Access',
    url: 'https://treasury.nt.gov.au/dtf/revenue/first-home-owner-grant',
    type: 'grants',
  },
  {
    state: 'NT',
    name: 'NT Government Gazette',
    url: 'https://gazette.nt.gov.au/',
    type: 'gazette',
  },
  {
    state: 'NT',
    name: 'NT Housing Policy',
    url: 'https://tfhc.nt.gov.au/housing',
    type: 'policy',
  },

  // === AUSTRALIAN CAPITAL TERRITORY ===
  {
    state: 'ACT',
    name: 'ACT Legislation - Property',
    url: 'https://www.legislation.act.gov.au/',
    type: 'legislation',
  },
  {
    state: 'ACT',
    name: 'ACT Revenue - Home Buyer Concession',
    url: 'https://www.revenue.act.gov.au/home-buyer-assistance',
    type: 'grants',
  },
  {
    state: 'ACT',
    name: 'ACT Government Gazette',
    url: 'https://www.legislation.act.gov.au/gazette/',
    type: 'gazette',
  },
  {
    state: 'ACT',
    name: 'ACT Housing Policy',
    url: 'https://www.act.gov.au/housing-and-home',
    type: 'policy',
  },
];
