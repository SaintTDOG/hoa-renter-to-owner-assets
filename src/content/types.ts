import { DailyDigest, PropertyUpdate, AustralianState } from '../types';

export interface EmailContent {
  subject: string;
  preheader: string;
  html: string;
  plainText: string;
}

export interface XPostContent {
  /** Primary post text (max 280 chars) */
  mainPost: string;
  /** Thread follow-ups for detail */
  thread: string[];
  /** Hashtags to append */
  hashtags: string[];
}

export interface FacebookPostContent {
  /** Post body text */
  body: string;
  /** Link to include */
  link: string;
  /** Suggested image alt text / description */
  imageDescription: string;
}

export interface ChannelContent {
  date: string;
  email: EmailContent;
  xPost: XPostContent;
  facebook: FacebookPostContent;
}

export interface ContentConfig {
  siteUrl: string;
  brandName: string;
  unsubscribeUrl: string;
  xHandle: string;
  facebookPage: string;
}

export const DEFAULT_CONFIG: ContentConfig = {
  siteUrl: 'https://rentertoowner.com.au',
  brandName: 'Renter to Owner',
  unsubscribeUrl: 'https://rentertoowner.com.au/unsubscribe',
  xHandle: '@RenterToOwnerAU',
  facebookPage: 'https://facebook.com/RenterToOwnerAU',
};
