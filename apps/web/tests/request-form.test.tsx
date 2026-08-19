import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ProjectRequestForm } from "@/components/forms";
import type { ServiceRecord } from "@/lib/types";

const service: ServiceRecord = {
  id: "service-id", slug: "api", title_en: "API Development", title_ar: "تطوير API",
  description_en: "Service", description_ar: "خدمة", related_skills: ["FastAPI"],
  included_items_en: [], included_items_ar: [], excluded_items_en: [], excluded_items_ar: [],
  client_requirements_en: [], client_requirements_ar: [], is_featured: false,
  availability_status: "available", publication_status: "published", starting_price: "100.00", shortest_delivery_days: 7,
  packages: [{ id: "package-id", service_id: "service-id", package_type: "standard", name_en: "Standard", name_ar: "قياسية", price: "100.00", currency: "USD", delivery_days: 7, revisions: 2, unlimited_revisions: false, included_deliverables_en: ["API"], included_deliverables_ar: ["API"], excluded_items_en: [], excluded_items_ar: [], client_requirements_en: [], client_requirements_ar: [], is_active: true, is_recommended: true, display_order: 1 }],
};

describe("project request form", () => {
  it("prefills the selected service and package", () => {
    render(<ProjectRequestForm locale="en" services={[service]} selectedServiceId="service-id" selectedPackageId="package-id" />);
    expect(screen.getByText("Selected package")).toBeInTheDocument();
    expect(screen.getByText("USD 100")).toBeInTheDocument();
    expect((screen.getByLabelText("Service") as HTMLSelectElement).value).toBe("service-id");
    expect((screen.getByLabelText("Package") as HTMLSelectElement).value).toBe("package-id");
  });

  it("supports the custom-offer path without a package selector", () => {
    render(<ProjectRequestForm locale="en" services={[service]} selectedServiceId="service-id" custom />);
    expect(screen.queryByLabelText("Package")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Request a custom offer" })).toBeInTheDocument();
  });
});
