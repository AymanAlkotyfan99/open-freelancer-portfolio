"use client";

import { ExternalLink, Github, Search } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useMemo, useState } from "react";

import type { Locale, ProjectRecord } from "@/lib/types";
import { Button } from "./ui/button";

export function ProjectBrowser({ projects, locale }: { projects: ProjectRecord[]; locale: Locale }) {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("all");
  const [skill, setSkill] = useState("all");
  const [sort, setSort] = useState<"newest" | "featured">("featured");
  const [shown, setShown] = useState(6);
  const categories = [...new Set(projects.map((item) => item.category).filter(Boolean))] as string[];
  const skills = [...new Set(projects.flatMap((item) => item.technologies))].sort();
  const visible = useMemo(() => projects.filter((item) => {
    const text = `${item.title_en} ${item.title_ar} ${item.summary_en} ${item.summary_ar}`.toLowerCase();
    return text.includes(search.toLowerCase()) && (category === "all" || item.category === category) && (skill === "all" || item.technologies.includes(skill));
  }).sort((a, b) => sort === "featured" ? Number(Boolean(b.is_featured)) - Number(Boolean(a.is_featured)) : String(b.project_date || "").localeCompare(String(a.project_date || ""))), [projects, search, category, skill, sort]);
  return <div>
    <div className="filter-bar">
      <label className="search-field"><Search size={18} /><span className="sr-only">{locale === "en" ? "Search projects" : "ابحث في المشاريع"}</span><input value={search} onChange={(event) => { setSearch(event.target.value); setShown(6); }} placeholder={locale === "en" ? "Search projects" : "ابحث في المشاريع"} /></label>
      <select aria-label={locale === "en" ? "Project category" : "تصنيف المشروع"} value={category} onChange={(event) => setCategory(event.target.value)}><option value="all">{locale === "en" ? "All categories" : "كل التصنيفات"}</option>{categories.map((item) => <option key={item}>{item}</option>)}</select>
      <select aria-label={locale === "en" ? "Project skill" : "مهارة المشروع"} value={skill} onChange={(event) => setSkill(event.target.value)}><option value="all">{locale === "en" ? "All skills" : "كل المهارات"}</option>{skills.map((item) => <option key={item}>{item}</option>)}</select>
      <select aria-label={locale === "en" ? "Sort projects" : "ترتيب المشاريع"} value={sort} onChange={(event) => setSort(event.target.value as "newest" | "featured")}><option value="featured">{locale === "en" ? "Featured first" : "المميزة أولاً"}</option><option value="newest">{locale === "en" ? "Newest" : "الأحدث"}</option></select>
    </div>
    {!visible.length ? <div className="empty-state"><Search /><h2>{locale === "en" ? "No matching projects" : "لا توجد مشاريع مطابقة"}</h2><p>{locale === "en" ? "Try a broader search or clear a filter." : "جرّب بحثاً أوسع أو أزل أحد عوامل التصفية."}</p></div> : <div className="project-cards">{visible.slice(0, shown).map((item) => <article className="portfolio-card" key={item.id || item.slug}>
      <Link className="card-media" href={`/${locale}/projects/${item.slug}`}>
        {item.cover_url ? <Image src={item.cover_url} alt={locale === "ar" ? item.title_ar : item.title_en} fill sizes="(max-width: 768px) 100vw, 50vw" /> : <div className="project-placeholder" aria-hidden><span>{item.technologies[0] || "AI"}</span></div>}
      </Link>
      <div className="card-body"><div className="card-meta"><span className="tag">{item.category || (locale === "en" ? "Project" : "مشروع")}</span>{(locale === "ar" ? item.status_ar : item.status_en) && <span>{locale === "ar" ? item.status_ar : item.status_en}</span>}</div>
        <h2><Link href={`/${locale}/projects/${item.slug}`}>{locale === "ar" ? item.title_ar : item.title_en}</Link></h2>
        <p>{(locale === "ar" ? item.short_description_ar : item.short_description_en) || (locale === "ar" ? item.summary_ar : item.summary_en)}</p>
        <div className="chips">{item.technologies.slice(0, 5).map((tech) => <span className="chip" key={tech}>{tech}</span>)}</div>
        <div className="card-actions"><Button asChild size="sm"><Link href={`/${locale}/projects/${item.slug}`}>{locale === "en" ? "View case study" : "عرض دراسة الحالة"}</Link></Button>{item.live_url && <Button asChild size="sm" variant="ghost"><a href={item.live_url} target="_blank" rel="noreferrer"><ExternalLink size={15} />{locale === "en" ? "Live" : "الموقع"}</a></Button>}{item.github_url && <Button asChild size="sm" variant="ghost"><a href={item.github_url} target="_blank" rel="noreferrer"><Github size={15} />GitHub</a></Button>}{item.demo_url && <Button asChild size="sm" variant="ghost"><a href={item.demo_url} target="_blank" rel="noreferrer">Demo</a></Button>}</div>
      </div>
    </article>)}</div>}
    {shown < visible.length && <div className="mt-10 text-center"><Button variant="outline" onClick={() => setShown((value) => value + 6)}>{locale === "en" ? "Load more projects" : "عرض مشاريع إضافية"}</Button></div>}
  </div>;
}
