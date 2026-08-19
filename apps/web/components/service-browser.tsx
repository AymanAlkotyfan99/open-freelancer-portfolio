"use client";

import { ArrowUpRight, Clock3, Search, Sparkles } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useMemo, useState } from "react";

import type { Locale, ServiceRecord } from "@/lib/types";
import { Button } from "./ui/button";

export function ServiceBrowser({ services, locale }: { services: ServiceRecord[]; locale: Locale }) {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("all");
  const [skill, setSkill] = useState("all");
  const [shown, setShown] = useState(6);
  const categories = [...new Set(services.map((item) => item.category).filter(Boolean))] as string[];
  const skills = [...new Set(services.flatMap((item) => item.related_skills))].sort();
  const visible = useMemo(() => services.filter((item) => {
    const text = `${item.title_en} ${item.title_ar} ${item.description_en} ${item.description_ar}`.toLowerCase();
    return text.includes(search.toLowerCase()) && (category === "all" || item.category === category) && (skill === "all" || item.related_skills.includes(skill));
  }), [services, search, category, skill]);
  return <div>
    <div className="filter-bar"><label className="search-field"><Search size={18} /><span className="sr-only">{locale === "en" ? "Search services" : "ابحث في الخدمات"}</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder={locale === "en" ? "Search services" : "ابحث في الخدمات"} /></label>
      <select value={category} onChange={(event) => setCategory(event.target.value)} aria-label={locale === "en" ? "Service category" : "تصنيف الخدمة"}><option value="all">{locale === "en" ? "All categories" : "كل التصنيفات"}</option>{categories.map((item) => <option key={item}>{item}</option>)}</select>
      <select value={skill} onChange={(event) => setSkill(event.target.value)} aria-label={locale === "en" ? "Service skill" : "مهارة الخدمة"}><option value="all">{locale === "en" ? "All skills" : "كل المهارات"}</option>{skills.map((item) => <option key={item}>{item}</option>)}</select>
    </div>
    {!visible.length ? <div className="empty-state"><Sparkles /><h2>{locale === "en" ? "No matching services" : "لا توجد خدمات مطابقة"}</h2><p>{locale === "en" ? "Try another search or filter." : "جرّب بحثاً أو تصنيفاً آخر."}</p></div> : <div className="service-cards">{visible.slice(0, shown).map((service) => <article className="service-card" key={service.id || service.slug}>
      <div className="service-visual">{service.cover_image_url ? <Image src={service.cover_image_url} alt="" fill sizes="(max-width: 768px) 100vw, 33vw" /> : <Sparkles aria-hidden />}</div>
      <div className="card-body"><div className="card-meta"><span className="tag">{service.category || (locale === "en" ? "Professional service" : "خدمة احترافية")}</span>{service.is_featured && <span className="featured-label">{locale === "en" ? "Featured" : "مميزة"}</span>}</div>
        <h2><Link href={`/${locale}/services/${service.slug}`}>{locale === "ar" ? service.title_ar : service.title_en}</Link></h2>
        <p>{(locale === "ar" ? service.short_description_ar : service.short_description_en) || (locale === "ar" ? service.description_ar : service.description_en)}</p>
        <div className="chips">{service.related_skills.slice(0, 5).map((item) => <span className="chip" key={item}>{item}</span>)}</div>
        <div className="service-facts">{service.starting_price !== null && service.starting_price !== undefined && <span>{locale === "en" ? "Starting from" : "يبدأ من"} <b>{service.packages.find((item) => item.is_active)?.currency} {Number(service.starting_price).toLocaleString(locale)}</b></span>}{service.shortest_delivery_days && <span><Clock3 size={15} />{service.shortest_delivery_days} {locale === "en" ? "days" : "أيام"}</span>}</div>
        <div className="card-actions"><Button asChild><Link href={`/${locale}/services/${service.slug}`}>{locale === "en" ? "View packages" : "عرض الباقات"}<ArrowUpRight size={16} /></Link></Button><Button asChild variant="outline"><Link href={`/${locale}/request-project?service=${service.id}&custom=1`}>{locale === "en" ? "Request service" : "اطلب الخدمة"}</Link></Button></div>
      </div>
    </article>)}</div>}
    {shown < visible.length && <div className="mt-10 text-center"><Button variant="outline" onClick={() => setShown((value) => value + 6)}>{locale === "en" ? "Load more services" : "عرض خدمات إضافية"}</Button></div>}
  </div>;
}
