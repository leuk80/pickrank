import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "PickRank — Finanz-Podcasts im Ranking",
    template: "%s | PickRank",
  },
  description:
    "PickRank verfolgt Stock-Empfehlungen aus Finanz-Podcasts und YouTube-Kanälen und rankt Creator nach ihrer messbaren Genauigkeit.",
  keywords: ["Finanz-Podcast", "Stock Picking", "Aktien", "DACH", "Ranking"],
  openGraph: {
    type: "website",
    locale: "de_DE",
    siteName: "PickRank",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="de" className={inter.variable}>
      <body className="min-h-screen bg-gray-50">
        <header className="border-b bg-white px-6 py-4">
          <nav className="mx-auto flex max-w-7xl items-center justify-between">
            <a href="/" className="text-xl font-bold text-brand-600">
              PickRank
            </a>
            <div className="flex gap-6 text-sm text-gray-600">
              <a href="/" className="hover:text-brand-600">
                Ranking
              </a>
              <a href="/recommendations" className="hover:text-brand-600">
                Empfehlungen
              </a>
              <a href="/admin" className="hover:text-brand-600 text-gray-400">
                Admin
              </a>
            </div>
          </nav>
        </header>

        <main className="mx-auto max-w-7xl px-6 py-8">{children}</main>

        <footer className="mt-16 border-t bg-white px-6 py-8 text-center text-sm text-gray-500">
          <p>
            PickRank ist kein Anlageberater. Alle Inhalte dienen
            ausschließlich Informationszwecken und stellen keine
            Anlageberatung dar.
          </p>
        </footer>
      </body>
    </html>
  );
}
