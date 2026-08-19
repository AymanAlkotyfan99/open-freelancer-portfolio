import { ArrowLeft, ArrowRight, ArrowUpRight, BriefcaseBusiness, Calendar, Check, Download, ExternalLink, Github, Linkedin, MapPin, Play, Send, Sparkles } from "lucide-react";
import Image from "next/image";
import Link from "next/link";

import { copy, projects as seededProjects, services as seededServiceNames, skillGroups } from "@/lib/content";
import type { Locale, PageResult, ProfileRecord, ProjectRecord, ServiceRecord } from "@/lib/types";
import { ContactForm, ProjectRequestForm } from "./forms";
import { MediaGallery } from "./media-gallery";
import { Reveal } from "./motion";
import { ProjectBrowser } from "./project-browser";
import { ServiceBrowser } from "./service-browser";
import { ServicePackages } from "./service-packages";
import { Button } from "./ui/button";

type Row = Record<string, unknown>;
const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

async function read<T>(path: string, fallback: T): Promise<T> {
  try {
    const seconds = Number(process.env.CONTENT_REVALIDATE_SECONDS ?? (process.env.NODE_ENV === "development" ? "0" : "60"));
    const response = await fetch(`${apiBase}${path}`, seconds === 0 ? { cache: "no-store" } : { next: { revalidate: seconds } });
    return response.ok ? await response.json() as T : fallback;
  } catch { return fallback; }
}

function projectFallbacks(): ProjectRecord[] {
  const en = seededProjects("en");
  const ar = seededProjects("ar");
  return en.map((item, index) => ({
    id: item.slug, slug: item.slug, title_en: item.title, title_ar: ar[index].title,
    summary_en: item.summary, summary_ar: ar[index].summary, category: item.category,
    status_en: item.status, status_ar: ar[index].status, technologies: item.tech,
    media: [], publication_status: "published", is_featured: index < 4,
  }));
}

async function managedProjects() {
  const data = await read<PageResult<ProjectRecord>>("/projects?paginated=true&page_size=50&sort=featured", { items: [], page: 1, page_size: 50, total: 0, pages: 0 });
  return data.items.length ? data.items : projectFallbacks();
}

async function managedServices() {
  const data = await read<PageResult<ServiceRecord>>("/services?paginated=true&page_size=50", { items: [], page: 1, page_size: 50, total: 0, pages: 0 });
  return data.items;
}

const localized = (row: Row | ProfileRecord, field: string, locale: Locale, fallback = "") => String(row[`${field}_${locale}`] ?? fallback);
const validLink = (value: unknown): value is string => typeof value === "string" && /^https:\/\//.test(value) && !value.includes("[");
const validMediaUrl = (value: unknown): value is string => typeof value === "string" && (/^https:\/\//.test(value) || /^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?\//.test(value)) && !value.includes("[");

function JsonLd({ data }: { data: Record<string, unknown> }) {
  return <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(data).replaceAll("<", "\\u003c") }} />;
}

function PageHead({ eyebrow, title, lead }: { eyebrow: string; title: string; lead: string }) {
  return <section className="page-head"><div className="shell"><p className="eyebrow">{eyebrow}</p><h1 className="h2">{title}</h1><p>{lead}</p></div></section>;
}

export async function Home({ locale }: { locale: Locale }) {
  const c = copy[locale];
  const [projects, services, profile, socialRows] = await Promise.all([
    managedProjects(), managedServices(), read<ProfileRecord>("/profile", {}), read<Row[]>("/social-links", []),
  ]);
  const name = localized(profile, "name", locale, "Ayman Naeem");
  const profileLinks = {
    github: profile.github_url, linkedin: profile.linkedin_url, upwork: profile.upwork_url,
    ...Object.fromEntries(socialRows.filter((row) => validLink(row.url)).map((row) => [String(row.platform).toLowerCase(), String(row.url)])),
  };
  const heroHeading = localized(profile, "hero_heading", locale, name);
  const statement = localized(profile, "hero_subheading", locale, localized(profile, "statement", locale, c.statement));
  return <main>
    <JsonLd data={{ "@context": "https://schema.org", "@type": "Person", name, jobTitle: localized(profile, "title", locale, c.title), description: statement, url: process.env.NEXT_PUBLIC_SITE_URL, image: validMediaUrl(profile.profile_image_url) ? profile.profile_image_url : undefined, sameAs: Object.values(profileLinks).filter(validLink) }} />
    <section className="hero"><div className="hero-backdrop" aria-hidden /><div className="shell hero-layout"><Reveal className="hero-copy">
      <p className="kicker"><i className="dot" />{String(profile.availability_status || c.available)}</p>
      <h1 className="display">{heroHeading}</h1><p className="hero-title">{localized(profile, "title", locale, c.title)}</p><p className="hero-intro">{statement}</p>
      <div className="actions"><Button asChild><Link href={`/${locale}/projects`}>{c.work}<ArrowUpRight size={16} /></Link></Button><Button asChild variant="outline"><Link href={`/${locale}/services`}>{locale === "en" ? "Explore services" : "استكشف الخدمات"}</Link></Button><Button asChild variant="outline"><Link href={`/${locale}/request-project`}>{c.hire}</Link></Button>{validLink(profile.cv_url) && <Button asChild variant="ghost"><a href={profile.cv_url} target="_blank" rel="noreferrer"><Download size={16} />{c.cv}</a></Button>}</div>
      <div className="social-row">{validLink(profileLinks.github) && <a className="icon-button glass" aria-label="GitHub" href={profileLinks.github} target="_blank" rel="noreferrer"><Github size={18} /></a>}{validLink(profileLinks.linkedin) && <a className="icon-button glass" aria-label="LinkedIn" href={profileLinks.linkedin} target="_blank" rel="noreferrer"><Linkedin size={18} /></a>}{validLink(profileLinks.upwork) && <a className="icon-button glass" aria-label="Upwork" href={profileLinks.upwork} target="_blank" rel="noreferrer"><BriefcaseBusiness size={18} /></a>}</div>
    </Reveal><Reveal className="portrait-wrap">{validMediaUrl(profile.profile_image_url) ? <div className="portrait-frame"><Image src={profile.profile_image_url} alt={localized(profile, "profile_image_alt", locale, name)} fill priority unoptimized sizes="(max-width: 768px) 82vw, 38vw" style={{ objectPosition: String(profile.profile_image_position || "50% 50%") }} /></div> : <div className="portrait-placeholder"><span>{name.split(" ").map((part) => part[0]).join("").slice(0, 2)}</span><Sparkles /></div>}</Reveal></div></section>
    <Reveal><section className="section"><div className="shell intro-grid"><div><p className="eyebrow">01 — {c.intro}</p><h2 className="h2">{c.intro}</h2></div><div><p className="lead-copy">{localized(profile, "about", locale, c.summary)}</p><div className="stats"><div className="stat"><b>AI</b><span>Agents · RAG · LLM</span></div><div className="stat"><b>API</b><span>Python · FastAPI</span></div><div className="stat"><b>Data</b><span>SQL · ETL · BI</span></div></div></div></div></section></Reveal>
    <Reveal><section className="section"><div className="shell"><div className="section-heading"><div><p className="eyebrow">02 — Portfolio</p><h2 className="h2">{c.selected}</h2></div><Link href={`/${locale}/projects`}>{c.allProjects}<ArrowUpRight size={16} /></Link></div><ProjectBrowser projects={projects.slice(0, 4)} locale={locale} /></div></section></Reveal>
    <Skills locale={locale} compact />
    <Reveal><section className="section"><div className="shell"><div className="section-heading"><div><p className="eyebrow">04 — {c.services}</p><h2 className="h2">{locale === "en" ? "Professional services, clearly scoped." : "خدمات احترافية بنطاق واضح."}</h2></div><Link href={`/${locale}/services`}>{locale === "en" ? "All services" : "كل الخدمات"}<ArrowUpRight size={16} /></Link></div>{services.length ? <div className="featured-services">{services.slice(0, 4).map((service) => <Link href={`/${locale}/services/${service.slug}`} className="featured-service" key={service.id}><Sparkles /><span>{locale === "ar" ? service.title_ar : service.title_en}</span><ArrowUpRight /></Link>)}</div> : <div className="featured-services">{seededServiceNames.slice(0, 4).map((name) => <div className="featured-service" key={name}><Sparkles /><span>{name}</span></div>)}</div>}</div></section></Reveal>
    <section className="section"><div className="shell cta-panel"><p className="eyebrow">{locale === "en" ? "Let’s build" : "لنبدأ البناء"}</p><h2 className="h2">{c.discuss}</h2><p>{localized(profile, "contact_cta", locale, c.discussText)}</p><div className="actions"><Button asChild><Link href={`/${locale}/request-project`}>{c.request}</Link></Button><Button asChild variant="outline"><Link href={`/${locale}/contact`}>{c.contact}</Link></Button></div></div></section>
  </main>;
}

export async function About({ locale }: { locale: Locale }) {
  const profile = await read<ProfileRecord>("/profile", {});
  const about = localized(profile, "about", locale, copy[locale].summary);
  return <main><PageHead eyebrow={locale === "en" ? "Profile / 02" : "الملف / 02"} title={locale === "en" ? "Production-minded across the stack." : "عقلية إنتاجية عبر كامل المنظومة."} lead={about} /><section className="section pt-4"><div className="shell about-grid"><article className="glass content-card"><h2>{locale === "en" ? "How I work" : "كيف أعمل"}</h2><p>{about}</p></article><article className="glass content-card"><h2>{String(profile.availability_status || copy[locale].available)}</h2>{localized(profile, "location", locale) && <p><MapPin size={18} />{localized(profile, "location", locale)}</p>}{profile.email && !String(profile.email).includes("[") && <p>{profile.email}</p>}</article></div></section></main>;
}

export async function Projects({ locale }: { locale: Locale }) {
  return <main><PageHead eyebrow={locale === "en" ? "Portfolio / 04" : "الأعمال / 04"} title={locale === "en" ? "Systems, platforms, and applied AI." : "أنظمة ومنصات وتطبيقات ذكاء اصطناعي."} lead={locale === "en" ? "Explore production engineering, research, client systems, and academic work." : "استكشف هندسة المنتجات والأبحاث وأنظمة العملاء والعمل الأكاديمي."} /><section className="section pt-4"><div className="shell"><ProjectBrowser projects={await managedProjects()} locale={locale} /></div></section></main>;
}

export async function ProjectDetail({ locale, slug }: { locale: Locale; slug: string }) {
  const project = await read<ProjectRecord | null>(`/projects/${slug}`, null) ?? projectFallbacks().find((item) => item.slug === slug);
  if (!project) return null;
  const title = locale === "ar" ? project.title_ar : project.title_en;
  const sections = [
    [locale === "en" ? "The problem" : "المشكلة", locale === "ar" ? project.problem_ar : project.problem_en],
    [locale === "en" ? "The solution" : "الحل", locale === "ar" ? project.solution_ar : project.solution_en],
    [locale === "en" ? "Main features" : "الميزات الرئيسية", (locale === "ar" ? project.features_ar : project.features_en)?.filter(Boolean)],
    [locale === "en" ? "Technical architecture" : "المعمارية التقنية", locale === "ar" ? project.architecture_ar : project.architecture_en],
    [locale === "en" ? "Challenges" : "التحديات", locale === "ar" ? project.challenges_ar : project.challenges_en],
    [locale === "en" ? "Implemented solutions" : "الحلول المنفذة", locale === "ar" ? project.implemented_solutions_ar : project.implemented_solutions_en],
    [locale === "en" ? "Results" : "النتائج", locale === "ar" ? project.results_ar : project.results_en],
  ].filter(([, value]) => Array.isArray(value) ? value.length : Boolean(value));
  const Back = locale === "ar" ? ArrowRight : ArrowLeft;
  return <main><section className="case-hero"><div className="shell"><Link className="back-link" href={`/${locale}/projects`}><Back size={16} />{copy[locale].projects}</Link><div className="case-grid"><div><p className="eyebrow">{project.category || (locale === "en" ? "Case study" : "دراسة حالة")}</p><h1 className="display">{title}</h1><p className="case-summary">{locale === "ar" ? project.summary_ar : project.summary_en}</p><div className="chips">{project.technologies.map((item) => <span className="chip" key={item}>{item}</span>)}</div><div className="actions">{project.live_url && <Button asChild><a href={project.live_url} target="_blank" rel="noreferrer"><ExternalLink size={16} />{locale === "en" ? "Live website" : "الموقع المباشر"}</a></Button>}{project.github_url && <Button asChild variant="outline"><a href={project.github_url} target="_blank" rel="noreferrer"><Github size={16} />GitHub</a></Button>}{project.demo_url && <Button asChild variant="outline"><a href={project.demo_url} target="_blank" rel="noreferrer"><Play size={16} />Demo</a></Button>}</div></div>{project.cover_url && <div className="case-cover"><Image src={project.cover_url} alt={title} fill priority sizes="(max-width: 768px) 100vw, 42vw" /></div>}</div></div></section>
    <JsonLd data={{ "@context": "https://schema.org", "@type": "CreativeWork", name: title, description: locale === "ar" ? project.summary_ar : project.summary_en, dateCreated: project.project_date || undefined, image: project.cover_url || undefined, url: `${process.env.NEXT_PUBLIC_SITE_URL || ""}/${locale}/projects/${project.slug}`, keywords: project.technologies.join(", ") }} />
    <section className="section pt-0"><div className="shell case-body"><aside className="case-facts">{project.project_date && <div><Calendar /><span>{new Date(project.project_date).toLocaleDateString(locale)}</span></div>}{(locale === "ar" ? project.role_ar : project.role_en) && <div><BriefcaseBusiness /><span>{locale === "ar" ? project.role_ar : project.role_en}</span></div>}{project.ownership_type && <span className="tag">{project.ownership_type}</span>}{(locale === "ar" ? project.development_duration_ar : project.development_duration_en) && <p>{locale === "ar" ? project.development_duration_ar : project.development_duration_en}</p>}</aside><div className="case-content">{sections.map(([heading, value]) => <section key={String(heading)}><h2>{String(heading)}</h2>{Array.isArray(value) ? <ul>{value.map((item) => <li key={item}><Check size={17} />{item}</li>)}</ul> : <p>{String(value)}</p>}</section>)}<MediaGallery media={project.media || []} locale={locale} /></div></div></section>
    <section className="section"><div className="shell cta-panel"><h2 className="h2">{locale === "en" ? "Have a similar project in mind?" : "هل لديك مشروع مشابه؟"}</h2><Button asChild><Link href={`/${locale}/request-project?referenceProject=${project.id}`}>{locale === "en" ? "Request a Similar Project" : "اطلب مشروعًا مشابهًا"}<ArrowUpRight size={16} /></Link></Button></div></section>
  </main>;
}

export async function Skills({ locale, compact = false }: { locale: Locale; compact?: boolean }) {
  const [skills, categories] = await Promise.all([read<Row[]>("/skills", []), read<Row[]>("/skill-categories", [])]);
  const groups = skills.length && categories.length ? categories.map((category) => [localized(category, "name", locale), skills.filter((skill) => skill.category_id === category.id).map((skill) => String(skill.name))] as const) : skillGroups;
  return <Reveal><section className="section"><div className="shell"><p className="eyebrow">Capabilities / 05</p><h2 className="h2 section-title">{locale === "en" ? "A structured toolkit for real systems." : "أدوات منظمة لبناء أنظمة حقيقية."}</h2><div className="skill-grid">{(compact ? groups.slice(0, 6) : groups).map(([name, items]) => <article className="glass skill-card" key={name}><h3>{name}</h3><div className="chips">{items.map((item) => <span className="chip" key={item}>{item}</span>)}</div></article>)}</div></div></section></Reveal>;
}

export async function Services({ locale, compact = false }: { locale: Locale; compact?: boolean }) {
  const services = await managedServices();
  if (compact) return <section className="section"><div className="shell"><ServiceBrowser services={services.slice(0, 6)} locale={locale} /></div></section>;
  return <main><PageHead eyebrow={locale === "en" ? "Services / 06" : "الخدمات / 06"} title={locale === "en" ? "From an ambiguous problem to operating software." : "من مشكلة غير واضحة إلى برمجيات عاملة."} lead={locale === "en" ? "Choose a clearly scoped package or request a custom offer for work that does not fit a standard tier." : "اختر باقة واضحة النطاق أو اطلب عرضاً مخصصاً لعمل لا يناسب باقة جاهزة."} /><section className="section pt-4"><div className="shell"><ServiceBrowser services={services} locale={locale} /></div></section></main>;
}

export async function ServiceDetail({ locale, slug }: { locale: Locale; slug: string }) {
  const service = await read<ServiceRecord | null>(`/services/${slug}`, null);
  if (!service) return null;
  const title = locale === "ar" ? service.title_ar : service.title_en;
  const Back = locale === "ar" ? ArrowRight : ArrowLeft;
  const inclusions = locale === "ar" && service.included_items_ar.length ? service.included_items_ar : service.included_items_en;
  const exclusions = locale === "ar" && service.excluded_items_ar.length ? service.excluded_items_ar : service.excluded_items_en;
  const requirements = locale === "ar" && service.client_requirements_ar.length ? service.client_requirements_ar : service.client_requirements_en;
  const offers = service.packages.filter((item) => item.is_active).map((item) => ({ "@type": "Offer", name: locale === "ar" ? item.name_ar : item.name_en, price: String(item.price), priceCurrency: item.currency, availability: "https://schema.org/InStock" }));
  return <main><section className="service-hero"><div className="shell"><Link className="back-link" href={`/${locale}/services`}><Back size={16} />{copy[locale].services}</Link><div className="service-hero-grid"><div><p className="eyebrow">{service.category || (locale === "en" ? "Professional service" : "خدمة احترافية")}</p><h1 className="display">{title}</h1><p className="case-summary">{(locale === "ar" ? service.short_description_ar : service.short_description_en) || (locale === "ar" ? service.description_ar : service.description_en)}</p><div className="chips">{service.related_skills.map((item) => <span className="chip" key={item}>{item}</span>)}</div><div className="actions"><Button asChild><a href="#packages">{locale === "en" ? "View packages" : "عرض الباقات"}</a></Button><Button asChild variant="outline"><Link href={`/${locale}/contact?subject=${encodeURIComponent(title)}`}><Send size={16} />{locale === "en" ? "Ask a question" : "اطرح سؤالاً"}</Link></Button><Button asChild variant="ghost"><Link href={`/${locale}/request-project?service=${service.id}&custom=1`}>{locale === "en" ? "Request a custom offer" : "اطلب عرضاً مخصصاً"}</Link></Button></div></div>{service.cover_image_url && <div className="case-cover"><Image src={service.cover_image_url} alt={title} fill priority sizes="(max-width: 768px) 100vw, 42vw" /></div>}</div></div></section>
    <JsonLd data={{ "@context": "https://schema.org", "@type": "ProfessionalService", name: title, description: locale === "ar" ? service.description_ar : service.description_en, areaServed: "Worldwide", offers: offers.length === 1 ? offers[0] : offers.length > 1 ? { "@type": "AggregateOffer", lowPrice: Math.min(...offers.map((offer) => Number(offer.price))), highPrice: Math.max(...offers.map((offer) => Number(offer.price))), priceCurrency: offers[0].priceCurrency, offerCount: offers.length, offers } : undefined }} />
    <section className="section pt-0"><div className="shell service-content"><div className="prose-wide"><p>{locale === "ar" ? service.description_ar : service.description_en}</p>{(locale === "ar" ? service.scope_ar : service.scope_en) && <section><h2>{locale === "en" ? "Scope of work" : "نطاق العمل"}</h2><p>{locale === "ar" ? service.scope_ar : service.scope_en}</p></section>}</div>{inclusions.length > 0 && <article className="content-card glass"><h2>{locale === "en" ? "What is included" : "ما هو مشمول"}</h2><ul>{inclusions.map((item) => <li key={item}><Check size={17} />{item}</li>)}</ul></article>}{exclusions.length > 0 && <article className="content-card glass"><h2>{locale === "en" ? "Not included" : "غير مشمول"}</h2><ul>{exclusions.map((item) => <li key={item}>{item}</li>)}</ul></article>}{requirements.length > 0 && <article className="content-card glass"><h2>{locale === "en" ? "What I need from you" : "ما أحتاجه منك"}</h2><ul>{requirements.map((item) => <li key={item}>{item}</li>)}</ul></article>}</div></section>
    <section id="packages" className="section packages-section"><div className="shell"><p className="eyebrow">{locale === "en" ? "Packages" : "الباقات"}</p><h2 className="h2 section-title">{locale === "en" ? "Choose the right scope." : "اختر النطاق المناسب."}</h2><ServicePackages serviceId={service.id} packages={service.packages} features={service.comparison?.features || []} locale={locale} /></div></section>
    {service.faqs && service.faqs.length > 0 && <section className="section"><div className="shell faq-list"><h2 className="h2 section-title">{locale === "en" ? "Frequently asked questions" : "الأسئلة الشائعة"}</h2>{service.faqs.map((faq) => <details key={faq.id}><summary>{locale === "ar" ? faq.question_ar : faq.question_en}</summary><p>{locale === "ar" ? faq.answer_ar : faq.answer_en}</p></details>)}</div></section>}
    {service.related_projects && service.related_projects.length > 0 && <section className="section"><div className="shell"><h2 className="h2 section-title">{locale === "en" ? "Related work" : "أعمال ذات صلة"}</h2><ProjectBrowser projects={service.related_projects} locale={locale} /></div></section>}
  </main>;
}

export async function Experience({ locale }: { locale: Locale }) {
  const [experience, education, activities] = await Promise.all([read<Row[]>("/experiences", []), read<Row[]>("/education", []), read<Row[]>("/activities", [])]);
  const rows = [...experience, ...education, ...activities];
  return <main><PageHead eyebrow={locale === "en" ? "Journey / 07" : "المسيرة / 07"} title={locale === "en" ? "Experience, education, and active learning." : "الخبرة والتعليم والتعلم المستمر."} lead={locale === "en" ? "A verified record of professional and academic growth." : "سجل موثّق للنمو المهني والأكاديمي."} /><section className="section pt-4"><div className="shell timeline">{rows.length ? rows.map((row, index) => <article key={String(row.id)}><span>{String(index + 1).padStart(2, "0")}</span><div><h2>{localized(row, "title", locale)}</h2><p>{localized(row, "description", locale)}</p></div></article>) : <div className="empty-state"><BriefcaseBusiness /><h2>{locale === "en" ? "Experience details are being updated" : "يجري تحديث تفاصيل الخبرة"}</h2></div>}</div></section></main>;
}

export function Contact({ locale }: { locale: Locale }) {
  return <main><PageHead eyebrow={locale === "en" ? "Contact / 08" : "تواصل / 08"} title={locale === "en" ? "Start with a clear conversation." : "ابدأ بمحادثة واضحة."} lead={locale === "en" ? "Tell me what you are building, improving, or untangling." : "أخبرني بما تريد بناءه أو تحسينه أو حلّه."} /><section className="section pt-4"><div className="shell max-w-3xl"><ContactForm locale={locale} /></div></section></main>;
}

export async function RequestProject({ locale, serviceId, packageId, referenceProjectId, custom }: { locale: Locale; serviceId?: string; packageId?: string; referenceProjectId?: string; custom?: boolean }) {
  const services = await managedServices();
  return <main><PageHead eyebrow={locale === "en" ? "Project brief / 09" : "ملخص المشروع / 09"} title={custom ? (locale === "en" ? "Request a custom offer." : "اطلب عرضاً مخصصاً.") : (locale === "en" ? "Give the project a strong starting point." : "امنح مشروعك نقطة بداية قوية.")} lead={locale === "en" ? "Share the goal, scope, and expected deliverables. You will receive a private, non-sequential reference number." : "شارك الهدف والنطاق والمخرجات المتوقعة، وستحصل على رقم مرجعي خاص وغير متسلسل."} /><section className="section pt-4"><div className="shell max-w-4xl"><ProjectRequestForm locale={locale} services={services} selectedServiceId={serviceId} selectedPackageId={packageId} referenceProjectId={referenceProjectId} custom={custom} /></div></section></main>;
}
