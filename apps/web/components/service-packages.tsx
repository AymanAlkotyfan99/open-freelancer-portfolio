"use client";

import { Check, Clock3, HelpCircle, Minus, Star, X } from "lucide-react";
import Link from "next/link";

import type { Locale, ServiceFeature, ServicePackage } from "@/lib/types";
import { Button } from "./ui/button";

function featureValue(feature: ServiceFeature, packageId: string, locale: Locale) {
  const value = feature.values.find((item) => item.package_id === packageId);
  if (!value) return <Minus aria-label={locale === "en" ? "Not specified" : "غير محدد"} size={16} />;
  if (feature.value_type === "boolean") return value.value_boolean ? <Check className="text-cyan" aria-label={locale === "en" ? "Included" : "مشمول"} size={18} /> : <X className="text-muted" aria-label={locale === "en" ? "Not included" : "غير مشمول"} size={18} />;
  if (feature.value_type === "number") return String(value.value_number ?? "—");
  return (locale === "ar" ? value.value_text_ar : value.value_text_en) || "—";
}

export function ServicePackages({ serviceId, packages, features, locale }: { serviceId: string; packages: ServicePackage[]; features: ServiceFeature[]; locale: Locale }) {
  const active = packages.filter((item) => item.is_active).sort((a, b) => a.display_order - b.display_order);
  if (!active.length) return <div className="empty-state"><HelpCircle /><h2>{locale === "en" ? "Packages are being configured" : "يجري إعداد الباقات"}</h2><p>{locale === "en" ? "Request a custom offer and describe what you need." : "اطلب عرضاً مخصصاً واشرح ما تحتاج إليه."}</p><Button asChild><Link href={`/${locale}/request-project?service=${serviceId}&custom=1`}>{locale === "en" ? "Request a custom offer" : "اطلب عرضاً مخصصاً"}</Link></Button></div>;
  return <>
    <div className="package-grid">{active.map((item) => {
      const included = locale === "ar" && item.included_deliverables_ar.length ? item.included_deliverables_ar : item.included_deliverables_en;
      const excluded = locale === "ar" && item.excluded_items_ar.length ? item.excluded_items_ar : item.excluded_items_en;
      return <article className={`package-card ${item.is_recommended ? "recommended" : ""}`} key={item.id}>{item.is_recommended && <span className="recommended-badge"><Star size={14} fill="currentColor" />{locale === "en" ? "Recommended" : "موصى بها"}</span>}
        <p className="eyebrow">{item.package_type}</p><h3>{locale === "ar" ? item.name_ar : item.name_en}</h3>{(locale === "ar" ? item.short_description_ar : item.short_description_en) && <p>{locale === "ar" ? item.short_description_ar : item.short_description_en}</p>}
        <div className="package-price"><span>{item.currency}</span><strong>{Number(item.price).toLocaleString(locale)}</strong></div>
        <div className="package-meta"><span><Clock3 size={16} />{item.delivery_days} {locale === "en" ? "day delivery" : "يوم للتسليم"}</span>{item.unlimited_revisions ? <span>{locale === "en" ? "Unlimited revisions" : "تعديلات غير محدودة"}</span> : item.revisions !== null && item.revisions !== undefined && <span>{item.revisions} {locale === "en" ? "revisions" : "تعديلات"}</span>}</div>
        {included.length > 0 && <ul className="package-list included">{included.map((text) => <li key={text}><Check size={16} />{text}</li>)}</ul>}{excluded.length > 0 && <ul className="package-list excluded">{excluded.map((text) => <li key={text}><X size={16} />{text}</li>)}</ul>}
        <Button asChild><Link href={`/${locale}/request-project?service=${serviceId}&package=${item.id}`}>{locale === "en" ? "Request this package" : "اطلب هذه الباقة"}</Link></Button>
      </article>;
    })}</div>
    {features.length > 0 && <section className="comparison-section" aria-labelledby="comparison-title"><h2 id="comparison-title" className="section-title">{locale === "en" ? "Compare package features" : "قارن ميزات الباقات"}</h2>
      <div className="comparison-desktop"><table><thead><tr><th>{locale === "en" ? "Feature" : "الميزة"}</th>{active.map((item) => <th key={item.id}>{locale === "ar" ? item.name_ar : item.name_en}</th>)}</tr></thead><tbody>{features.map((feature) => <tr key={feature.id}><th>{locale === "ar" ? feature.name_ar : feature.name_en}</th>{active.map((item) => <td key={item.id}>{featureValue(feature, item.id, locale)}</td>)}</tr>)}</tbody></table></div>
      <div className="comparison-mobile">{features.map((feature) => <article key={feature.id}><h3>{locale === "ar" ? feature.name_ar : feature.name_en}</h3>{active.map((item) => <div key={item.id}><span>{locale === "ar" ? item.name_ar : item.name_en}</span><b>{featureValue(feature, item.id, locale)}</b></div>)}</article>)}</div>
    </section>}
  </>;
}
