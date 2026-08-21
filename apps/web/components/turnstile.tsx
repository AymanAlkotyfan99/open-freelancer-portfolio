"use client";

import Script from "next/script";
import { useEffect, useId, useRef } from "react";

import type { Locale } from "@/lib/types";

declare global {
  interface Window { turnstile?: { render: (element: HTMLElement, options: Record<string, unknown>) => string; remove: (id: string) => void } }
}

export function Turnstile({ locale, onToken }: { locale: Locale; onToken: (token: string) => void }) {
  const siteKey = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY;
  const elementId = `turnstile-${useId().replaceAll(":", "")}`;
  const widget = useRef<string | null>(null);
  useEffect(() => {
    if (!siteKey) return;
    const render = () => {
      const element = document.getElementById(elementId);
      if (element && window.turnstile && !widget.current) widget.current = window.turnstile.render(element, { sitekey: siteKey, language: locale, callback: onToken, "expired-callback": () => onToken(""), "error-callback": () => onToken(""), "timeout-callback": () => onToken("") });
    };
    const timer = window.setInterval(render, 250);
    render();
    return () => { window.clearInterval(timer); if (widget.current && window.turnstile) window.turnstile.remove(widget.current); };
  }, [elementId, locale, onToken, siteKey]);
  if (!siteKey) return null;
  return <><Script src="https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit" strategy="afterInteractive" /><div id={elementId} /></>;
}
