import path from "node:path";

import type { NextConfig } from "next";

const isProductionDeployment = process.env.APP_ENVIRONMENT === "production";

function configuredUrl(name: "NEXT_PUBLIC_API_URL" | "NEXT_PUBLIC_SITE_URL", fallback: string): URL {
  const value = process.env[name] || fallback;
  let url: URL;
  try {
    url = new URL(value);
  } catch {
    throw new Error(`${name} must be an absolute URL`);
  }
  if (isProductionDeployment && url.protocol !== "https:") {
    throw new Error(`${name} must use HTTPS when APP_ENVIRONMENT=production`);
  }
  if (url.username || url.password || url.search || url.hash) {
    throw new Error(`${name} must not include credentials, a query, or a fragment`);
  }
  if (isProductionDeployment && name === "NEXT_PUBLIC_SITE_URL" && url.pathname !== "/") {
    throw new Error("NEXT_PUBLIC_SITE_URL must be an origin without a path");
  }
  if (isProductionDeployment && name === "NEXT_PUBLIC_API_URL" && url.pathname !== "/api/v1") {
    throw new Error("NEXT_PUBLIC_API_URL must end exactly with /api/v1");
  }
  return url;
}

const apiUrl = configuredUrl("NEXT_PUBLIC_API_URL", "http://localhost:8000/api/v1");
configuredUrl("NEXT_PUBLIC_SITE_URL", "http://localhost:3000");
if (isProductionDeployment && !process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY) {
  throw new Error("NEXT_PUBLIC_TURNSTILE_SITE_KEY is required when APP_ENVIRONMENT=production");
}

const scriptSources = [
  "'self'",
  "'unsafe-inline'",
  ...(process.env.NODE_ENV === "development" ? ["'unsafe-eval'"] : []),
  "https://challenges.cloudflare.com",
].join(" ");
const connectSources = [
  "'self'",
  apiUrl.origin,
  "https://challenges.cloudflare.com",
  ...(process.env.NODE_ENV === "development" ? ["http://localhost:8000", "http://127.0.0.1:8000"] : []),
].filter((value, index, values) => values.indexOf(value) === index).join(" ");
const imageSources = ["'self'", "blob:", "data:", apiUrl.origin, "https://res.cloudinary.com"]
  .filter((value, index, values) => values.indexOf(value) === index).join(" ");
const mediaSources = ["'self'", "blob:", apiUrl.origin, "https://res.cloudinary.com"]
  .filter((value, index, values) => values.indexOf(value) === index).join(" ");
const csp = [
  "default-src 'self'",
  "base-uri 'self'",
  "object-src 'none'",
  "frame-ancestors 'none'",
  `img-src ${imageSources}`,
  `media-src ${mediaSources}`,
  `script-src ${scriptSources}`,
  "frame-src https://challenges.cloudflare.com https://www.youtube.com https://www.youtube-nocookie.com https://player.vimeo.com",
  `connect-src ${connectSources}`,
  "style-src 'self' 'unsafe-inline'",
  "font-src 'self' data:",
  "form-action 'self'",
  ...(isProductionDeployment ? ["upgrade-insecure-requests"] : []),
].join("; ");

const nextConfig: NextConfig = {
  output: "standalone",
  outputFileTracingRoot: path.resolve(process.cwd()),
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "res.cloudinary.com" },
      ...(!isProductionDeployment && ["http:", "https:"].includes(apiUrl.protocol)
        ? [{
            protocol: apiUrl.protocol.replace(":", "") as "http" | "https",
            hostname: apiUrl.hostname,
            port: apiUrl.port,
          }]
        : []),
    ],
  },
  async headers() {
    return [{
      source: "/(.*)",
      headers: [
        { key: "X-Content-Type-Options", value: "nosniff" },
        { key: "X-Frame-Options", value: "DENY" },
        { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
        { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
        { key: "Content-Security-Policy", value: csp },
        ...(isProductionDeployment
          ? [{ key: "Strict-Transport-Security", value: "max-age=31536000; includeSubDomains" }]
          : []),
      ],
    }];
  },
};

export default nextConfig;
