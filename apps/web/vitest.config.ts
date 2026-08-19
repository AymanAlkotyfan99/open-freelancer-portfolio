import path from "node:path";
import { defineConfig } from "vitest/config";

export default defineConfig({
  root: process.cwd(),
  cacheDir: ".vitest",
  esbuild: { jsx: "automatic" },
  test: { environment: "jsdom", include: ["tests/**/*.test.{ts,tsx}"], setupFiles: ["./tests/setup.ts"] },
  resolve: { alias: { "@": path.resolve(process.cwd()) } },
});
