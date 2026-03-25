import { DailyDigest } from '../types';
import { ChannelContent, ContentConfig, DEFAULT_CONFIG } from './types';
import { generateEmail } from './email-template';
import { generateXPost } from './x-post';
import { generateFacebookPost } from './facebook-post';

/**
 * Generates CRO-optimized content for all channels from a daily digest.
 * Each channel format follows platform-specific best practices for engagement.
 */
export function generateAllContent(
  digest: DailyDigest,
  config: ContentConfig = DEFAULT_CONFIG
): ChannelContent {
  return {
    date: digest.date,
    email: generateEmail(digest, config),
    xPost: generateXPost(digest, config),
    facebook: generateFacebookPost(digest, config),
  };
}

export { generateEmail } from './email-template';
export { generateXPost } from './x-post';
export { generateFacebookPost } from './facebook-post';
export { DEFAULT_CONFIG } from './types';
export type { ChannelContent, ContentConfig, EmailContent, XPostContent, FacebookPostContent } from './types';
