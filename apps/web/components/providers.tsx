"use client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "next-themes";
import { useState } from "react";

import { ApiError } from "@/lib/api";

export function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(() => new QueryClient({ defaultOptions: { queries: {
    retry: (failureCount, error) => !(error instanceof ApiError && error.status < 500) && failureCount < 2,
  } } }));
  return <ThemeProvider attribute="class" defaultTheme="dark" enableSystem><QueryClientProvider client={client}>{children}</QueryClientProvider></ThemeProvider>;
}
