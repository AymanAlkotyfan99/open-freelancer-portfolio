import { expect, test, type APIRequestContext } from "@playwright/test";

const apiBase = "http://127.0.0.1:8000/api/v1";

async function adminLogin(request: APIRequestContext) {
  const response = await request.post(`${apiBase}/auth/login`, {
    data: { email: "admin@example.com", password: "PortfolioE2E!123" },
  });
  expect(response.ok()).toBeTruthy();
}

test.describe.serial("portfolio journeys", () => {
  test("a project without media or optional links renders safely", async ({ page }) => {
    await page.goto("/en/projects/e2e-no-media");
    await expect(page.getByRole("heading", { name: "E2E Project Without Media" })).toBeVisible();
    await expect(page.getByRole("main").locator("img")).toHaveCount(0);
    await expect(page.getByRole("link", { name: "Live website" })).toHaveCount(0);
    await expect(page.getByRole("link", { name: "GitHub" })).toHaveCount(0);
    await expect(page.getByRole("link", { name: "Demo" })).toHaveCount(0);
  });

  test("a client compares tiers and submits the selected package", async ({ page }) => {
    await page.goto("/en/services/e2e-ai-service");
    await expect(page.getByRole("heading", { name: "E2E AI Service" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Basic" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Standard" })).toBeVisible();
    await expect(page.getByText("Deployment guide").first()).toBeVisible();
    const requestLink = page.locator(".package-card").filter({ hasText: "Standard" }).getByRole("link", { name: "Request this package" });
    const href = await requestLink.getAttribute("href");
    expect(href).toContain("service=");
    expect(href).toContain("package=");
    await page.goto(href!);
    await expect(page).toHaveURL(/package=/);
    const query = new URL(page.url()).searchParams;
    const serviceValues = await page.getByLabel("Service").locator("option").evaluateAll((options) => options.map((option) => (option as HTMLOptionElement).value));
    expect(serviceValues).toContain(query.get("service"));
    await page.getByLabel("Service").selectOption(query.get("service")!);
    await page.getByLabel("Package").selectOption(query.get("package")!);
    await expect(page.getByText("Selected package")).toBeVisible();
    await page.getByLabel("Full name").fill("E2E Client");
    await page.getByRole("textbox", { name: "Email", exact: true }).fill("client@example.com");
    await page.getByLabel("Project title").fill("Package request journey");
    await page.getByLabel("Detailed project description").fill("This is a sufficiently detailed browser journey for a package request.");
    await page.getByText("I consent to being contacted about this inquiry.").click();
    const responsePromise = page.waitForResponse((response) => response.url().endsWith("/project-requests") && response.request().method() === "POST");
    await page.getByRole("button", { name: "Submit package request" }).click();
    const response = await responsePromise;
    expect({ status: response.status(), body: await response.text() }).toEqual(expect.objectContaining({ status: 201 }));
    await expect(page.getByRole("status")).toContainText("Request saved. Reference");
  });

  test("an admin creates and publishes a project without an image", async ({ page }) => {
    await page.goto("/admin");
    await page.getByLabel("Email").fill("admin@example.com");
    await page.getByLabel("Password").fill("PortfolioE2E!123");
    await page.getByRole("button", { name: "Sign in" }).click();
    await page.getByRole("button", { name: "Projects", exact: true }).click();
    await page.getByRole("button", { name: "New project" }).click();
    await page.getByLabel("English name *").fill("Admin Published Project");
    await page.getByLabel("Arabic name *").fill("مشروع منشور من الإدارة");
    await page.getByLabel("Slug *").fill("admin-published-project");
    await page.getByLabel("Skills / technologies *").fill("Next.js, FastAPI");
    await page.getByLabel("English description *").fill("Created through the purpose-built admin browser journey.");
    await page.getByLabel("Arabic description *").fill("تم إنشاؤه عبر رحلة متصفح لوحة الإدارة.");
    await page.getByLabel("Publication").selectOption("published");
    await page.getByRole("button", { name: "Save project" }).click();
    await expect(page.getByText("Project media")).toBeVisible();
    await page.goto("/en/projects/admin-published-project");
    await expect(page.getByRole("heading", { name: "Admin Published Project" })).toBeVisible();
  });

  test("an admin creates a service and package that appear publicly", async ({ request, page }) => {
    await adminLogin(request);
    const serviceResponse = await request.post(`${apiBase}/admin/services`, {
      data: {
        slug: "admin-created-service",
        title_en: "Admin Created Service",
        title_ar: "خدمة منشأة من الإدارة",
        description_en: "A published service created through the authenticated admin API.",
        description_ar: "خدمة منشورة أُنشئت عبر واجهة الإدارة الموثقة.",
        related_skills: ["Next.js"],
        publication_status: "published",
        availability_status: "available",
      },
    });
    expect(serviceResponse.ok()).toBeTruthy();
    const service = await serviceResponse.json();
    const packageResponse = await request.post(`${apiBase}/admin/services/${service.id}/packages`, {
      data: {
        package_type: "standard",
        name_en: "Launch",
        name_ar: "إطلاق",
        price: "700.00",
        currency: "USD",
        delivery_days: 14,
        revisions: 2,
        included_deliverables_en: ["Production deployment"],
        included_deliverables_ar: ["نشر إنتاجي"],
        is_active: true,
      },
    });
    expect(packageResponse.ok()).toBeTruthy();
    await page.goto("/en/services/admin-created-service");
    await expect(page.getByRole("heading", { name: "Admin Created Service" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Launch" })).toBeVisible();
    await expect(page.locator(".package-price")).toContainText("700");
  });

  test("a saved request keeps its original price after an admin price change", async ({ request, page }) => {
    await adminLogin(request);
    const services = await (await request.get(`${apiBase}/services?paginated=false`)).json();
    const service = services.find((item: { slug: string }) => item.slug === "e2e-ai-service");
    const standard = service.packages.find((item: { package_type: string }) => item.package_type === "standard");
    const submitted = await request.post(`${apiBase}/project-requests`, {
      data: {
        client_name: "Snapshot Client",
        email: "snapshot@example.com",
        preferred_contact_method: "email",
        service_id: service.id,
        package_id: standard.id,
        displayed_price: "0.01",
        currency: "FAKE",
        delivery_days: 999,
        project_title: "Snapshot browser journey",
        project_description: "A detailed request that verifies immutable server-owned commercial data.",
        expected_deliverables: "Working system",
        consent: true,
      },
    });
    expect(submitted.ok()).toBeTruthy();
    const reference = (await submitted.json()).reference;
    const changed = await request.patch(`${apiBase}/admin/packages/${standard.id}`, {
      data: {
        package_type: standard.package_type,
        name_en: standard.name_en,
        name_ar: standard.name_ar,
        price: "999.00",
        currency: standard.currency,
        delivery_days: standard.delivery_days,
        revisions: standard.revisions,
        included_deliverables_en: standard.included_deliverables_en,
        included_deliverables_ar: standard.included_deliverables_ar,
        excluded_items_en: standard.excluded_items_en,
        excluded_items_ar: standard.excluded_items_ar,
        client_requirements_en: standard.client_requirements_en,
        client_requirements_ar: standard.client_requirements_ar,
        unlimited_revisions: standard.unlimited_revisions,
        is_active: standard.is_active,
        is_recommended: standard.is_recommended,
        display_order: standard.display_order,
      },
    });
    expect(changed.ok()).toBeTruthy();

    await page.goto("/admin");
    await page.getByLabel("Email").fill("admin@example.com");
    await page.getByLabel("Password").fill("PortfolioE2E!123");
    await page.getByRole("button", { name: "Sign in" }).click();
    await page.getByRole("button", { name: "Requests", exact: true }).click();
    await page.getByText(reference).click();
    await expect(page.getByText("USD 425.00", { exact: true }).last()).toBeVisible();
  });
});
