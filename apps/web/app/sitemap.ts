import type { MetadataRoute } from "next";

import { projects as fallbackProjects } from "@/lib/content";
import type { PageResult, ProjectRecord, ServiceRecord } from "@/lib/types";

const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

async function records<T>(path: string): Promise<T[]> {
  try { const response = await fetch(`${apiBase}${path}`, { next: { revalidate: 3600 } }); return response.ok ? ((await response.json()) as PageResult<T>).items : []; }
  catch { return []; }
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const base = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";
  const paths = ["", "about", "skills", "projects", "services", "experience", "contact", "request-project", "privacy"];
  const [projects, services] = await Promise.all([records<ProjectRecord>("/projects?paginated=true&page_size=50"), records<ServiceRecord>("/services?paginated=true&page_size=50")]);
  const projectSlugs = projects.length ? projects.map((item) => item.slug) : fallbackProjects("en").map((item) => item.slug);
  return (["en", "ar"] as const).flatMap((locale) => [
    ...paths.map((path) => ({ url: `${base}/${locale}${path ? `/${path}` : ""}`, lastModified: new Date() })),
    ...projectSlugs.map((slug) => ({ url: `${base}/${locale}/projects/${slug}`, lastModified: new Date() })),
    ...services.map((service) => ({ url: `${base}/${locale}/services/${service.slug}`, lastModified: new Date() })),
  ]);
}
