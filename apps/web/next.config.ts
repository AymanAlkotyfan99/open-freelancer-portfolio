import type { NextConfig } from "next";
import path from "node:path";

const scriptSources = [
  "'self'",
  "'unsafe-inline'",
  ...(process.env.NODE_ENV === "development" ? ["'unsafe-eval'"] : []),
  "https://challenges.cloudflare.com",
].join(" ");
const configuredApiOrigin = (() => {
  try { return new URL(process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1").origin; }
  catch { return ""; }
})();
const connectSources = [
  "'self'",
  configuredApiOrigin,
  ...(process.env.NODE_ENV === "development" ? ["http://localhost:8000", "http://127.0.0.1:8000"] : []),
  "https:",
].filter(Boolean).filter((value, index, values) => values.indexOf(value) === index).join(" ");
const imageSources = ["'self'", "blob:", "data:", configuredApiOrigin, "https://res.cloudinary.com"]
  .filter(Boolean).filter((value, index, values) => values.indexOf(value) === index).join(" ");

const nextConfig: NextConfig = {
  output: "standalone",
  outputFileTracingRoot: path.resolve(process.cwd()),
  images: { remotePatterns: [{ protocol: "https", hostname: "res.cloudinary.com" }] },
  async headers() {
    return [{ source: "/(.*)", headers: [
      { key: "X-Content-Type-Options", value: "nosniff" }, { key: "X-Frame-Options", value: "DENY" },
      { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
      { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
      { key: "Content-Security-Policy", value: `default-src 'self'; img-src ${imageSources}; script-src ${scriptSources}; frame-src https://challenges.cloudflare.com; connect-src ${connectSources}; style-src 'self' 'unsafe-inline'; font-src 'self' data:` }
    ] }];
  }
};
export default nextConfig;
