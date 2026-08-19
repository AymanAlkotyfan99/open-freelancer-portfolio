import type { Config } from "tailwindcss";
export default { darkMode: "class", content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"], theme: { extend: { colors: { ink: "#07101f", cyan: "#45d8e8", violet: "#9b87f5" }, fontFamily: { sans: ["var(--font-sans)", "Arial", "sans-serif"] } } }, plugins: [] } satisfies Config;

