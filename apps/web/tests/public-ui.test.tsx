import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MediaGallery } from "@/components/media-gallery";
import { ProjectBrowser } from "@/components/project-browser";
import { ServicePackages } from "@/components/service-packages";
import type { ProjectRecord, ServiceFeature, ServicePackage } from "@/lib/types";

const projects: ProjectRecord[] = [
  { id: "one", slug: "without-image", title_en: "Project without image", title_ar: "مشروع بلا صورة", summary_en: "A resilient optional-media card.", summary_ar: "بطاقة تدعم الوسائط الاختيارية.", category: "Backend", status_en: "Completed", status_ar: "مكتمل", github_url: null, live_url: null, demo_url: null, technologies: ["FastAPI"], media: [], is_featured: true },
  { id: "two", slug: "frontend", title_en: "Frontend project", title_ar: "مشروع واجهة", summary_en: "React application.", summary_ar: "تطبيق React.", category: "Frontend", technologies: ["React"], media: [] },
];

const packages: ServicePackage[] = [
  { id: "basic", service_id: "service", package_type: "basic", name_en: "Basic", name_ar: "أساسية", price: "100.00", currency: "USD", delivery_days: 5, revisions: 1, unlimited_revisions: false, included_deliverables_en: ["Source code"], included_deliverables_ar: ["الشيفرة المصدرية"], excluded_items_en: [], excluded_items_ar: [], client_requirements_en: [], client_requirements_ar: [], is_active: true, is_recommended: false, display_order: 0 },
  { id: "standard", service_id: "service", package_type: "standard", name_en: "Standard", name_ar: "قياسية", price: "250.00", currency: "USD", delivery_days: 10, revisions: 3, unlimited_revisions: false, included_deliverables_en: ["Source code", "Deployment"], included_deliverables_ar: ["الشيفرة المصدرية", "النشر"], excluded_items_en: [], excluded_items_ar: [], client_requirements_en: [], client_requirements_ar: [], is_active: true, is_recommended: true, display_order: 1 },
  { id: "premium", service_id: "service", package_type: "premium", name_en: "Premium", name_ar: "مميزة", price: "500.00", currency: "USD", delivery_days: 15, revisions: 5, unlimited_revisions: false, included_deliverables_en: ["Full delivery"], included_deliverables_ar: ["تسليم كامل"], excluded_items_en: [], excluded_items_ar: [], client_requirements_en: [], client_requirements_ar: [], is_active: false, is_recommended: false, display_order: 2 },
];
const features: ServiceFeature[] = [{ id: "feature", name_en: "Deployment", name_ar: "النشر", value_type: "boolean", values: [{ package_id: "basic", value_boolean: false }, { package_id: "standard", value_boolean: true }] }];

describe("public project UI", () => {
  it("renders an elegant fallback and hides absent optional links", () => {
    render(<ProjectBrowser projects={projects} locale="en" />);
    expect(screen.getByText("Project without image")).toBeInTheDocument();
    expect(screen.queryByText("GitHub")).not.toBeInTheDocument();
    expect(screen.queryByText("Live")).not.toBeInTheDocument();
  });

  it("searches and filters projects", () => {
    render(<ProjectBrowser projects={projects} locale="en" />);
    fireEvent.change(screen.getByPlaceholderText("Search projects"), { target: { value: "Frontend" } });
    expect(screen.getByText("Frontend project")).toBeInTheDocument();
    expect(screen.queryByText("Project without image")).not.toBeInTheDocument();
  });

  it("renders image and video gallery controls", () => {
    render(<MediaGallery locale="en" media={[{ id: "image", media_type: "image", source_type: "upload", secure_url: "https://res.cloudinary.com/demo/image/upload/example.jpg", alt_text_en: "Dashboard screenshot", is_cover: true, sort_order: 0 }, { id: "video", media_type: "video", source_type: "external_url", secure_url: "https://www.youtube.com/watch?v=abc", title_en: "Demo video", is_cover: false, sort_order: 1 }]} />);
    expect(screen.getByLabelText("Open Dashboard screenshot")).toBeInTheDocument();
    expect(screen.getByLabelText("Play Project media")).toBeInTheDocument();
  });
});

describe("service package UI", () => {
  it("shows active packages, hides inactive tiers, and renders comparison values", () => {
    render(<ServicePackages serviceId="service" packages={packages} features={features} locale="en" />);
    expect(screen.getAllByText("Basic").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Standard").length).toBeGreaterThan(0);
    expect(screen.queryByText("Premium")).not.toBeInTheDocument();
    expect(screen.getAllByText("Deployment").length).toBeGreaterThan(0);
  });

  it("renders localized Arabic package content", () => {
    render(<div dir="rtl"><ServicePackages serviceId="service" packages={packages} features={features} locale="ar" /></div>);
    expect(screen.getAllByText("أساسية").length).toBeGreaterThan(0);
    expect(screen.getAllByText("النشر").length).toBeGreaterThan(0);
  });
});
