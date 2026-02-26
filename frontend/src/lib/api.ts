import type {
  Creator,
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
