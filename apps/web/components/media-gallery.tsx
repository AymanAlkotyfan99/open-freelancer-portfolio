"use client";

import Image from "next/image";
import { Play, X } from "lucide-react";
import { useEffect, useState } from "react";

import type { Locale, ProjectMedia } from "@/lib/types";

function embedUrl(value: string) {
  try {
    const url = new URL(value);
    if (url.hostname === "youtu.be") return `https://www.youtube-nocookie.com/embed/${url.pathname.slice(1)}`;
    if (url.hostname.includes("youtube.com")) return `https://www.youtube-nocookie.com/embed/${url.searchParams.get("v") ?? ""}`;
    if (url.hostname.includes("vimeo.com")) return `https://player.vimeo.com/video/${url.pathname.split("/").filter(Boolean).at(-1)}`;
  } catch { return ""; }
  return "";
}

export function MediaGallery({ media, locale }: { media: ProjectMedia[]; locale: Locale }) {
  const [active, setActive] = useState<ProjectMedia | null>(null);
  useEffect(() => {
    if (!active) return;
    const close = (event: KeyboardEvent) => event.key === "Escape" && setActive(null);
    document.addEventListener("keydown", close);
    document.body.style.overflow = "hidden";
    return () => { document.removeEventListener("keydown", close); document.body.style.overflow = ""; };
  }, [active]);
  if (!media.length) return null;
  return <section aria-labelledby="project-gallery"><h2 id="project-gallery" className="section-title">{locale === "en" ? "Project gallery" : "معرض المشروع"}</h2>
    <div className="gallery-grid">{media.map((item) => {
      const alt = (locale === "ar" ? item.alt_text_ar : item.alt_text_en) || (locale === "ar" ? "وسائط المشروع" : "Project media");
      return <button className="gallery-item" key={item.id} onClick={() => setActive(item)} aria-label={item.media_type === "video" ? `${locale === "en" ? "Play" : "تشغيل"} ${alt}` : `${locale === "en" ? "Open" : "فتح"} ${alt}`}>
        {item.thumbnail_url || item.media_type === "image" ? <Image src={item.thumbnail_url || item.secure_url} alt={alt} fill sizes="(max-width: 768px) 100vw, 50vw" /> : <div className="media-placeholder"><Play /></div>}
        {item.media_type === "video" && <span className="play-badge"><Play size={18} fill="currentColor" /></span>}
      </button>;
    })}</div>
    {active && <div className="lightbox" role="dialog" aria-modal="true" aria-label={locale === "en" ? "Media preview" : "معاينة الوسائط"} onClick={() => setActive(null)}>
      <button className="lightbox-close" onClick={() => setActive(null)} aria-label={locale === "en" ? "Close" : "إغلاق"}><X /></button>
      <div className="lightbox-content" onClick={(event) => event.stopPropagation()}>
        {active.media_type === "image" ? <Image src={active.secure_url} alt={(locale === "ar" ? active.alt_text_ar : active.alt_text_en) || ""} width={1600} height={1000} sizes="95vw" /> : active.source_type === "external_url" ? <iframe src={embedUrl(active.secure_url)} title={(locale === "ar" ? active.title_ar : active.title_en) || "Project video"} allow="fullscreen; picture-in-picture" allowFullScreen /> : <video src={active.secure_url} controls preload="metadata" playsInline />}
        {(locale === "ar" ? active.caption_ar : active.caption_en) && <p>{locale === "ar" ? active.caption_ar : active.caption_en}</p>}
      </div>
    </div>}
  </section>;
}
