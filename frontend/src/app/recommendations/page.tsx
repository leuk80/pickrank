import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Empfehlungen",
};

export default function RecommendationsPage() {
  return (
    <div>
      <h1 className="mb-2 text-3xl font-bold text-gray-900">
        Aktuelle Empfehlungen
      </h1>
      <p className="mb-8 text-gray-500">
        Alle extrahierten BUY/HOLD/SELL-Empfehlungen aus Finanz-Podcasts und
        YouTube-Kanälen.
      </p>
      {/* TODO Phase 4: fetch and render paginated recommendations */}
      <div className="rounded-lg border bg-white p-8 text-center text-gray-400">
        Daten werden geladen…
      </div>
    </div>
  );
}
