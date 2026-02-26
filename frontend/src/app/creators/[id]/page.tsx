import type { Metadata } from "next";

// Next.js 15: dynamic segment params are a Promise and must be awaited.
interface PageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { id } = await params;
  return {
    title: `Creator ${id}`,
  };
}

export default async function CreatorDetailPage({ params }: PageProps) {
  const { id } = await params;

  return (
    <div>
      <h1 className="mb-2 text-3xl font-bold text-gray-900">Creator Detail</h1>
      <p className="mb-8 text-sm text-gray-400">ID: {id}</p>
      {/* TODO Phase 4: fetch creator details and render picks + performance */}
      <div className="rounded-lg border bg-white p-8 text-center text-gray-400">
        Daten werden geladen…
      </div>
    </div>
  );
}
