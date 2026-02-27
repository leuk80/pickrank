"use client";

import { useState } from "react";
import {
  adminCreateCreator,
  adminIngestCreator,
  adminListCreators,
  adminListEpisodes,
  adminListRecommendations,
} from "@/lib/api";
import type {
  AdminCreator,
  AdminEpisode,
  AdminRecommendation,
  IngestResult,
  Language,
  Platform,
} from "@/lib/types";

// ---------------------------------------------------------------------------
// Small UI primitives
// ---------------------------------------------------------------------------

function Badge({
  children,
  color = "gray",
}: {
  children: React.ReactNode;
  color?: "green" | "red" | "yellow" | "blue" | "gray";
}) {
  const colors = {
    green: "bg-green-100 text-green-800",
    red: "bg-red-100 text-red-800",
    yellow: "bg-yellow-100 text-yellow-800",
    blue: "bg-blue-100 text-blue-800",
    gray: "bg-gray-100 text-gray-700",
  };
  return (
    <span
      className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-medium ${colors[color]}`}
    >
      {children}
    </span>
  );
}

function typeBadge(type: string) {
  if (type === "BUY") return <Badge color="green">BUY</Badge>;
  if (type === "SELL") return <Badge color="red">SELL</Badge>;
  return <Badge color="yellow">HOLD</Badge>;
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function AdminPage() {
  const [apiKey, setApiKey] = useState("");
  const [keyConfirmed, setKeyConfirmed] = useState(false);

  const [creators, setCreators] = useState<AdminCreator[]>([]);
  const [loadingCreators, setLoadingCreators] = useState(false);

  // New creator form
  const [form, setForm] = useState({
    name: "",
    platform: "youtube" as Platform,
    language: "de" as Language,
    rss_url: "",
    youtube_channel_id: "",
  });
  const [formError, setFormError] = useState("");
  const [formLoading, setFormLoading] = useState(false);

  // Ingestion
  const [ingestLoading, setIngestLoading] = useState<string | null>(null);
  const [ingestResults, setIngestResults] = useState<Record<string, IngestResult>>({});

  // Episodes
  const [selectedCreator, setSelectedCreator] = useState<AdminCreator | null>(null);
  const [episodes, setEpisodes] = useState<AdminEpisode[]>([]);
  const [loadingEpisodes, setLoadingEpisodes] = useState(false);

  // Recommendations
  const [selectedEpisode, setSelectedEpisode] = useState<AdminEpisode | null>(null);
  const [recommendations, setRecommendations] = useState<AdminRecommendation[]>([]);
  const [loadingRecs, setLoadingRecs] = useState(false);

  const [globalError, setGlobalError] = useState("");

  // ---------------------------------------------------------------------------

  async function loadCreators() {
    setLoadingCreators(true);
    setGlobalError("");
    try {
      const data = await adminListCreators(apiKey);
      setCreators(data);
    } catch (e: unknown) {
      setGlobalError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoadingCreators(false);
    }
  }

  function confirmKey() {
    if (!apiKey.trim()) return;
    setKeyConfirmed(true);
    loadCreators();
  }

  async function handleCreateCreator(e: React.FormEvent) {
    e.preventDefault();
    setFormError("");
    if (!form.name.trim()) { setFormError("Name ist erforderlich"); return; }
    if (form.platform === "youtube" && !form.youtube_channel_id.trim()) {
      setFormError("YouTube Channel ID ist erforderlich");
      return;
    }
    if (form.platform === "podcast" && !form.rss_url.trim()) {
      setFormError("RSS URL ist erforderlich");
      return;
    }
    setFormLoading(true);
    try {
      await adminCreateCreator(apiKey, {
        name: form.name,
        platform: form.platform,
        language: form.language,
        rss_url: form.rss_url || undefined,
        youtube_channel_id: form.youtube_channel_id || undefined,
      });
      setForm({ name: "", platform: "youtube", language: "de", rss_url: "", youtube_channel_id: "" });
      await loadCreators();
    } catch (e: unknown) {
      setFormError(e instanceof Error ? e.message : String(e));
    } finally {
      setFormLoading(false);
    }
  }

  async function handleIngest(creator: AdminCreator) {
    setIngestLoading(creator.id);
    setGlobalError("");
    try {
      const result = await adminIngestCreator(apiKey, creator.id);
      setIngestResults((prev) => ({ ...prev, [creator.id]: result }));
      await loadCreators();
    } catch (e: unknown) {
      setGlobalError(e instanceof Error ? e.message : String(e));
    } finally {
      setIngestLoading(null);
    }
  }

  async function handleShowEpisodes(creator: AdminCreator) {
    setSelectedCreator(creator);
    setSelectedEpisode(null);
    setRecommendations([]);
    setLoadingEpisodes(true);
    try {
      const data = await adminListEpisodes(apiKey, creator.id);
      setEpisodes(data);
    } catch (e: unknown) {
      setGlobalError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoadingEpisodes(false);
    }
  }

  async function handleShowRecommendations(episode: AdminEpisode) {
    setSelectedEpisode(episode);
    setLoadingRecs(true);
    try {
      const data = await adminListRecommendations(apiKey, episode.id);
      setRecommendations(data);
    } catch (e: unknown) {
      setGlobalError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoadingRecs(false);
    }
  }

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  if (!keyConfirmed) {
    return (
      <div className="mx-auto max-w-sm pt-24">
        <h1 className="mb-6 text-2xl font-bold text-gray-900">
          Phase 2 – Test Interface
        </h1>
        <div className="rounded-lg border bg-white p-6 shadow-sm">
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Admin API Key
          </label>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && confirmKey()}
            placeholder="Aus .env → ADMIN_API_KEY"
            className="mb-4 w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
          />
          <button
            onClick={confirmKey}
            className="w-full rounded bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-500"
          >
            Anmelden
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">
          Phase 2 – Test Interface
        </h1>
        <button
          onClick={loadCreators}
          disabled={loadingCreators}
          className="rounded border border-gray-300 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50 disabled:opacity-50"
        >
          {loadingCreators ? "Lädt…" : "Aktualisieren"}
        </button>
      </div>

      {globalError && (
        <div className="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {globalError}
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Creator hinzufügen                                                  */}
      {/* ------------------------------------------------------------------ */}
      <section className="rounded-lg border bg-white p-6">
        <h2 className="mb-4 text-lg font-semibold text-gray-800">
          Creator hinzufügen
        </h2>
        <form onSubmit={handleCreateCreator} className="space-y-3">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <input
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Name (z.B. Finanzfluss)"
              className="rounded border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
            />
            <select
              value={form.platform}
              onChange={(e) =>
                setForm({ ...form, platform: e.target.value as Platform })
              }
              className="rounded border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
            >
              <option value="youtube">YouTube</option>
              <option value="podcast">Podcast (RSS)</option>
            </select>
            <select
              value={form.language}
              onChange={(e) =>
                setForm({ ...form, language: e.target.value as Language })
              }
              className="rounded border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
            >
              <option value="de">Deutsch</option>
              <option value="en">English</option>
            </select>
          </div>
          {form.platform === "youtube" ? (
            <input
              value={form.youtube_channel_id}
              onChange={(e) =>
                setForm({ ...form, youtube_channel_id: e.target.value })
              }
              placeholder="YouTube Channel ID (z.B. UCxxxxxx)"
              className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
            />
          ) : (
            <input
              value={form.rss_url}
              onChange={(e) => setForm({ ...form, rss_url: e.target.value })}
              placeholder="RSS Feed URL (z.B. https://example.com/feed.xml)"
              className="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
            />
          )}
          {formError && (
            <p className="text-sm text-red-600">{formError}</p>
          )}
          <button
            type="submit"
            disabled={formLoading}
            className="rounded bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-500 disabled:opacity-50"
          >
            {formLoading ? "Wird gespeichert…" : "Creator hinzufügen"}
          </button>
        </form>
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* Creator-Liste                                                        */}
      {/* ------------------------------------------------------------------ */}
      <section className="rounded-lg border bg-white">
        <div className="border-b px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-800">
            Creator ({creators.length})
          </h2>
        </div>
        {creators.length === 0 ? (
          <p className="px-6 py-8 text-center text-sm text-gray-400">
            Noch keine Creator. Füge oben einen hinzu.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
                <tr>
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3">Platform</th>
                  <th className="px-4 py-3">Sprache</th>
                  <th className="px-4 py-3 text-right">Episoden</th>
                  <th className="px-4 py-3 text-right">Recs</th>
                  <th className="px-4 py-3 text-right">Unverarbeitet</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {creators.map((c) => {
                  const result = ingestResults[c.id];
                  return (
                    <tr key={c.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium text-gray-900">
                        {c.name}
                      </td>
                      <td className="px-4 py-3">
                        <Badge color={c.platform === "youtube" ? "red" : "blue"}>
                          {c.platform}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-gray-500">{c.language}</td>
                      <td className="px-4 py-3 text-right text-gray-700">
                        {c.episode_count}
                      </td>
                      <td className="px-4 py-3 text-right text-gray-700">
                        {c.recommendation_count}
                      </td>
                      <td className="px-4 py-3 text-right">
                        {c.unprocessed_count > 0 ? (
                          <Badge color="yellow">{c.unprocessed_count}</Badge>
                        ) : (
                          <span className="text-gray-400">–</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => handleShowEpisodes(c)}
                            className="rounded border border-gray-300 px-2.5 py-1 text-xs text-gray-600 hover:bg-gray-50"
                          >
                            Episoden
                          </button>
                          <button
                            onClick={() => handleIngest(c)}
                            disabled={ingestLoading === c.id}
                            className="rounded bg-brand-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-brand-500 disabled:opacity-50"
                          >
                            {ingestLoading === c.id ? "Läuft…" : "Ingest"}
                          </button>
                        </div>
                        {result && (
                          <p className="mt-1 text-right text-xs text-gray-500">
                            +{result.new_episodes} Eps · +{result.recommendations_saved} Recs
                            {result.errors.length > 0 && (
                              <span className="text-red-500">
                                {" "}· {result.errors.length} Fehler
                              </span>
                            )}
                          </p>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* Episoden                                                             */}
      {/* ------------------------------------------------------------------ */}
      {selectedCreator && (
        <section className="rounded-lg border bg-white">
          <div className="border-b px-6 py-4">
            <h2 className="text-lg font-semibold text-gray-800">
              Episoden – {selectedCreator.name}
            </h2>
          </div>
          {loadingEpisodes ? (
            <p className="px-6 py-8 text-center text-sm text-gray-400">
              Lädt…
            </p>
          ) : episodes.length === 0 ? (
            <p className="px-6 py-8 text-center text-sm text-gray-400">
              Keine Episoden. Starte Ingest.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
                  <tr>
                    <th className="px-4 py-3">Titel</th>
                    <th className="px-4 py-3">Datum</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3 text-right">Recs</th>
                    <th className="px-4 py-3"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {episodes.map((ep) => (
                    <tr key={ep.id} className="hover:bg-gray-50">
                      <td className="max-w-xs truncate px-4 py-3 font-medium text-gray-900">
                        {ep.title}
                      </td>
                      <td className="px-4 py-3 text-gray-500">
                        {ep.publish_date ?? "–"}
                      </td>
                      <td className="px-4 py-3">
                        {ep.processed ? (
                          <Badge color="green">Verarbeitet</Badge>
                        ) : (
                          <Badge color="yellow">Ausstehend</Badge>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right text-gray-700">
                        {ep.recommendation_count}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => handleShowRecommendations(ep)}
                          className="rounded border border-gray-300 px-2.5 py-1 text-xs text-gray-600 hover:bg-gray-50"
                        >
                          Recommendations
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Recommendations                                                      */}
      {/* ------------------------------------------------------------------ */}
      {selectedEpisode && (
        <section className="rounded-lg border bg-white">
          <div className="border-b px-6 py-4">
            <h2 className="text-lg font-semibold text-gray-800">
              Recommendations
            </h2>
            <p className="mt-0.5 truncate text-sm text-gray-500">
              {selectedEpisode.title}
            </p>
          </div>
          {loadingRecs ? (
            <p className="px-6 py-8 text-center text-sm text-gray-400">
              Lädt…
            </p>
          ) : recommendations.length === 0 ? (
            <p className="px-6 py-8 text-center text-sm text-gray-400">
              Keine Recommendations für diese Episode.
            </p>
          ) : (
            <div className="divide-y">
              {recommendations.map((rec) => (
                <div key={rec.id} className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <span className="text-lg font-bold text-gray-900">
                      {rec.ticker}
                    </span>
                    {typeBadge(rec.type)}
                    {rec.company_name && (
                      <span className="text-sm text-gray-500">
                        {rec.company_name}
                      </span>
                    )}
                    {rec.confidence !== null && (
                      <span className="ml-auto text-xs text-gray-400">
                        Confidence: {(rec.confidence * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>
                  {rec.sentence && (
                    <p className="mt-1.5 text-sm italic text-gray-600">
                      &ldquo;{rec.sentence}&rdquo;
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
