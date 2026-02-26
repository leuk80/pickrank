import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    // In development, proxy /api/* to the local FastAPI server.
    // In production on Vercel, NEXT_PUBLIC_API_URL should be unset (same host)
    // or set to the Vercel backend deployment URL.
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
