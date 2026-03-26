import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactCompiler: true,
  allowedDevOrigins: ["127.0.0.1", "localhost"],
  /**
   * Dev-only: proxy /api/* to FastAPI so the browser stays same-origin with the Next app.
   * Then Set-Cookie from the backend is stored for localhost:3000 (refresh token works).
   * Pair with NEXT_PUBLIC_API_URL=http://localhost:3000 in .env.development.
   */
  async rewrites() {
    if (process.env.NODE_ENV !== "development") {
      return [];
    }
    return [
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8000/api/:path*",
      },
    ];
  },
};

export default nextConfig;
