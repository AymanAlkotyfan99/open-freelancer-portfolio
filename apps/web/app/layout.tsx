import type { Metadata } from "next";

import { Providers } from "@/components/providers";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000"),
  title: {
    default: "Ayman Naeem — AI Software Engineer",
    template: "%s · Ayman Naeem",
  },
  description:
    "Production-ready AI systems, scalable backend services, automation, data engineering, and full-stack applications.",
  openGraph: {
    title: "Ayman Naeem — AI Software Engineer",
    description: "Production-ready AI and full-stack engineering.",
    type: "website",
    images: [{ url: "/og.png", width: 1200, height: 630, alt: "Ayman Naeem — AI Software Engineer" }],
  },
  twitter: { card: "summary_large_image", images: ["/og.png"] },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en" suppressHydrationWarning>
    <body suppressHydrationWarning><Providers>{children}</Providers></body>
  </html>;
}
