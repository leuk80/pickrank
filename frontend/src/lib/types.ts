// TypeScript interfaces mirroring the backend Pydantic schemas.
// Keep in sync manually until a code generator is introduced.

export type Platform = "youtube" | "podcast";
export type Language = "de" | "en";
export type RecommendationType = "BUY" | "HOLD" | "SELL";

export interface CreatorScore {
  total_picks: number;
  hit_rate: number | null;
  avg_outperformance: number | null;
  overall_score: number | null;
  updated_at: string; // ISO 8601
}

export interface Creator {
  id: string;
  name: string;
  platform: Platform;
  rss_url: string | null;
  youtube_channel_id: string | null;
  language: Language;
  created_at: string;
  score: CreatorScore | null;
}

export interface Recommendation {
  id: string;
  episode_id: string;
  ticker: string;
  company_name: string | null;
  type: RecommendationType;
  confidence: number | null;
  sentence: string | null;
  recommendation_date: string | null; // ISO 8601 date
  created_at: string;
}

export interface RankedCreator {
  rank: number;
  creator_id: string;
  name: string;
  platform: Platform;
  language: Language;
  total_picks: number;
  hit_rate: number | null;
  avg_outperformance: number | null;
  overall_score: number | null;
  updated_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
}

export interface PaginatedRecommendations extends PaginatedResponse<Recommendation> {
  page: number;
  page_size: number;
}

export interface RankingResponse extends PaginatedResponse<RankedCreator> {
  minimum_picks_required: number;
}
