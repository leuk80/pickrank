import type {
  AdminCreator,
  AdminEpisode,
  AdminRecommendation,
  Creator,
  IngestResult,
  Language,
  Platform,
  PaginatedRecommendations,
  PaginatedResponse,
  RankedCreator,
  RankingResponse,
} from "./types";

// In production, NEXT_PUBLIC_API_URL is unset (same Vercel host).
// In development, Next.js rewrites /api/* to the local FastAPI server.
const API_BASE = process.env.NEXT_PUBLIC_API_URL
  ? `${process.env.NEXT_PUBLIC_API_URL}/api`
  : "/api";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API error ${response.status}: ${await response.text()}`);
  }

  return response.json() as Promise<T>;
}

export async function getCreators(
  page = 1,
  pageSize = 20
): Promise<PaginatedResponse<Creator>> {
  return apiFetch(`/creators?page=${page}&page_size=${pageSize}`);
}

export async function getCreator(id: string): Promise<Creator> {
  return apiFetch(`/creators/${id}`);
}

export async function getRecommendations(
  page = 1,
  pageSize = 20,
  ticker?: string,
  type?: string
): Promise<PaginatedRecommendations> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  if (ticker) params.set("ticker", ticker);
  if (type) params.set("type", type);
  return apiFetch(`/recommendations?${params.toString()}`);
}

export async function getRanking(
  limit = 50,
  language?: string
): Promise<RankingResponse> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (language) params.set("language", language);
  return apiFetch(`/ranking?${params.toString()}`);
}

export async function subscribe(
  email: string,
  language = "de"
): Promise<{ message: string; email: string }> {
  return apiFetch("/subscribe", {
    method: "POST",
    body: JSON.stringify({ email, language }),
  });
}

// ---------------------------------------------------------------------------
// Admin API (Phase 2 test interface) – requires X-Admin-Key header
// ---------------------------------------------------------------------------

function adminFetch<T>(
  path: string,
  adminKey: string,
  options?: RequestInit
): Promise<T> {
  return apiFetch<T>(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-Admin-Key": adminKey,
      ...(options?.headers ?? {}),
    },
  });
}

export async function adminListCreators(
  adminKey: string
): Promise<AdminCreator[]> {
  return adminFetch("/admin/creators", adminKey);
}

export async function adminCreateCreator(
  adminKey: string,
  payload: {
    name: string;
    platform: Platform;
    language: Language;
    rss_url?: string;
    youtube_channel_id?: string;
  }
): Promise<AdminCreator> {
  return adminFetch("/admin/creators", adminKey, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function adminIngestCreator(
  adminKey: string,
  creatorId: string
): Promise<IngestResult> {
  return adminFetch(`/admin/ingest/${creatorId}`, adminKey, { method: "POST" });
}

export async function adminListEpisodes(
  adminKey: string,
  creatorId: string
): Promise<AdminEpisode[]> {
  return adminFetch(`/admin/episodes/${creatorId}`, adminKey);
}

export async function adminListRecommendations(
  adminKey: string,
  episodeId: string
): Promise<AdminRecommendation[]> {
  return adminFetch(`/admin/recommendations/${episodeId}`, adminKey);
}
