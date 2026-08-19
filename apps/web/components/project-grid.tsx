"use client";

import { useState } from "react";

import type { Locale, Project } from "@/lib/content";
import Link from "next/link";

export function ProjectGrid({ projects, locale }: { projects: Project[]; locale: Locale }) {
  const [filter, setFilter] = useState("All");
  const categories = ["All", ...new Set(projects.map((project) => project.category))];
  const visible = filter === "All" ? projects : projects.filter((project) => project.category === filter);
  return <>
    <div className="mb-8 flex flex-wrap gap-2" aria-label="Project filters">
      {categories.map((category) => <button className={`tag ${filter === category ? "border-cyan text-cyan" : ""}`} onClick={() => setFilter(category)} key={category}>{category}</button>)}
    </div>
    <div className="cards">{visible.map((project) => <Link className="project-card" href={`/${locale}/projects/${project.slug}`} key={project.slug}>
      <span className="tag">{project.category}</span><div className="mt-auto">
        <p className="mb-3 text-xs uppercase tracking-widest text-cyan">{project.status}</p>
        <h2 className="text-2xl font-semibold">{project.title}</h2>
        <p className="mt-3 leading-6 text-muted">{project.summary}</p>
        <div className="chips">{project.tech.slice(0, 5).map((tech) => <span className="chip" key={tech}>{tech}</span>)}</div>
      </div>
    </Link>)}</div>
  </>;
}
