"use client";

import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function ErrorPage({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <main className="section"><div className="shell empty-state"><AlertTriangle /><h1>Something went wrong</h1><p>The page could not be loaded. Please try again.</p><Button onClick={reset}>Try again</Button></div></main>;
}
