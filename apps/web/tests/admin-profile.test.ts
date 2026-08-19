import { afterEach, describe, expect, it, vi } from "vitest";

import { api } from "@/lib/api";
import { buildProfilePatch } from "@/lib/profile-payload";

describe("profile saving", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("sends only editable fields that changed", () => {
    const original = { id: "profile-id", name_en: "Ayman", email: "[EMAIL]", cv_url: "[CV_URL]" };

    expect(buildProfilePatch({ ...original, name_en: "  Ayman Naeem  " }, original)).toEqual({
      name_en: "Ayman Naeem",
    });
  });

  it("surfaces FastAPI validation details", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({
      detail: [{ loc: ["body", "email"], msg: "value is not a valid email address" }],
    }), { status: 422, headers: { "Content-Type": "application/json" } })));

    await expect(api("/admin/profile", { method: "PATCH", body: "{}" }))
      .rejects.toThrow("email: value is not a valid email address");
  });

  it("refreshes an expired session and retries the original request", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ detail: "Invalid session" }), { status: 401 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ message: "Session refreshed" }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ name_en: "Ayman" }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(api<{ name_en: string }>("/admin/profile")).resolves.toEqual({ name_en: "Ayman" });
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(fetchMock.mock.calls[1][0]).toBe("http://localhost:8000/api/v1/auth/refresh");
    expect(fetchMock.mock.calls[2][0]).toBe("http://localhost:8000/api/v1/admin/profile");
  });

  it("does not override the multipart boundary for photo uploads", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ profile_image_url: "https://example.com/photo.png" }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    const body = new FormData();
    body.append("file", new Blob(["photo"], { type: "image/png" }), "photo.png");

    await api("/admin/profile/photo", { method: "POST", body });

    const headers = fetchMock.mock.calls[0][1]?.headers as Headers;
    expect(headers.has("Content-Type")).toBe(false);
  });
});
