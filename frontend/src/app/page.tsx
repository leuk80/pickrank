import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Ranking",
};

export default function RankingPage() {
  return (
    <div>
      <h1 className="mb-2 text-3xl font-bold text-gray-900">
        Creator Ranking
      </h1>
      <p className="mb-8 text-gray-500">
        Ranked nach Genauigkeit der Stock-Empfehlungen. Mindestens 20 Picks
        erforderlich.
      </p>
      {/* TODO Phase 4: fetch and render ranked creators */}
      <div className="rounded-lg border bg-white p-8 text-center text-gray-400">
        Daten werden geladen…
      </div>
    </div>
  );
}
