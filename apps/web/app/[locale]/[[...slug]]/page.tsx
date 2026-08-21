import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { About, Contact, Experience, Home, ProjectDetail, Projects, RequestProject, ServiceDetail, Services, Skills } from "@/components/pages";
import { projects } from "@/lib/content";
import type { Locale, ProjectRecord, ServiceRecord } from "@/lib/types";

const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
const isProductionDeployment = process.env.APP_ENVIRONMENT === "production";

async function metadataRecord(path: string) {
  try { const seconds = Number(process.env.CONTENT_REVALIDATE_SECONDS ?? "300"); const response = await fetch(`${apiBase}${path}`, seconds === 0 ? { cache: "no-store" } : { next: { revalidate: seconds } }); return response.ok ? await response.json() as ProjectRecord | ServiceRecord : null; }
  catch { return null; }
}

export async function generateMetadata({ params }: { params: Promise<{ locale: string; slug?: string[] }> }): Promise<Metadata> {
  const { locale, slug = [] } = await params;
  let title = slug[0] ? slug[0].replaceAll("-", " ") : "AI Software Engineer";
  let description: string | undefined;
  let image: string | undefined;
  if (slug[0] === "projects" && slug[1]) {
    const record = await metadataRecord(`/projects/${slug[1]}`) as ProjectRecord | null;
    const fallback = !isProductionDeployment ? projects(locale as Locale).find((item) => item.slug === slug[1]) : undefined;
    title = record ? (locale === "ar" ? record.title_ar : record.title_en) : fallback?.title || title;
    description = record ? (locale === "ar" ? record.short_description_ar || record.summary_ar : record.short_description_en || record.summary_en) : fallback?.summary;
    image = record?.cover_url || undefined;
  }
  if (slug[0] === "services" && slug[1]) {
    const record = await metadataRecord(`/services/${slug[1]}`) as ServiceRecord | null;
    if (record) { title = locale === "ar" ? record.title_ar : record.title_en; description = locale === "ar" ? record.short_description_ar || record.description_ar : record.short_description_en || record.description_en; image = record.cover_image_url || undefined; }
  }
  const canonical = `/${locale}/${slug.join("/")}`.replace(/\/$/, "");
  return { title, description, alternates: { canonical, languages: { en: `/en/${slug.join("/")}`, ar: `/ar/${slug.join("/")}` } }, openGraph: { title, description, images: image ? [image] : undefined }, twitter: { card: "summary_large_image", title, description, images: image ? [image] : undefined } };
}

export default async function Page({ params, searchParams }: { params: Promise<{ locale: string; slug?: string[] }>; searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const { locale: raw, slug = [] } = await params;
  const locale = raw as Locale;
  if (!(["en", "ar"] as string[]).includes(locale)) notFound();
  if (!slug.length) return <Home locale={locale} />;
  if (slug[0] === "projects" && slug[1]) return <ProjectDetail locale={locale} slug={slug[1]} />;
  if (slug[0] === "services" && slug[1]) return <ServiceDetail locale={locale} slug={slug[1]} />;
  const query = await searchParams;
  const value = (key: string) => typeof query[key] === "string" ? query[key] : undefined;
  switch (slug[0]) {
    case "about": return <About locale={locale} />;
    case "skills": return <Skills locale={locale} />;
    case "projects": return <Projects locale={locale} />;
    case "services": return <Services locale={locale} />;
    case "experience": return <Experience locale={locale} />;
    case "contact": return <Contact locale={locale} />;
    case "request-project": return <RequestProject locale={locale} serviceId={value("service")} packageId={value("package")} referenceProjectId={value("referenceProject")} custom={value("custom") === "1"} />;
    case "privacy": return <main><section className="page-head"><div className="shell prose-wide"><p className="eyebrow">Privacy</p><h1 className="h2">{locale === "en" ? "Privacy policy" : "سياسة الخصوصية"}</h1><p>{locale === "en" ? "Inquiry data is used only to respond, evaluate requests, maintain security, and operate this portfolio. It is never sold." : "تُستخدم بيانات الاستفسارات للرد وتقييم الطلبات وحماية وتشغيل الموقع فقط، ولا تُباع."}</p></div></section></main>;
    default: notFound();
  }
}
