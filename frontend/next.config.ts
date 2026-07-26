import type { NextConfig } from "next";

const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  {
    key: "Referrer-Policy",
    value: "strict-origin-when-cross-origin",
  },
  {
    key: "Permissions-Policy",
    value: "camera=(), microphone=(), geolocation=()",
  },
];

if (process.env.NODE_ENV === "production") {
  securityHeaders.push({
    key: "Strict-Transport-Security",
    value: "max-age=63072000; includeSubDomains; preload",
  });
}

const nextConfig: NextConfig = {
  reactCompiler: true,
  allowedDevOrigins: ["127.0.0.1", "localhost"],
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "images.unsplash.com",
        pathname: "/**",
      },
    ],
  },
  /**
   * Account list used to live at exact `/bookings`. Guest checkout keeps
   * `/bookings/success`, `/bookings/cancel`, `/bookings/:id/confirm`.
   */
  async redirects() {
    return [
      {
        source: "/bookings",
        destination: "/account/bookings",
        permanent: true,
      },
    ];
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: securityHeaders,
      },
    ];
  },

  /**
   * Same-origin API proxy (dev + prod).
   *
   * Browser → NEXT_PUBLIC_API_URL (Next origin) → rewrite → API_UPSTREAM_URL.
   * Set-Cookie lands on the web origin so CSRF double-submit can read csrf_token.
   * Stripe webhooks stay on the API host (/webhooks/* is outside this rewrite).
   */
  async rewrites() {
    const upstream = (process.env.API_UPSTREAM_URL ?? "")
      .trim()
      .replace(/\/$/, "");
    if (!upstream) {
      return [];
    }
    return [
      {
        source: "/api/:path*",
        destination: `${upstream}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
