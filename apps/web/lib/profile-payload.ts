import type { ProfileRecord } from "@/lib/types";

const editableProfileFields = [
  "name_en",
  "name_ar",
  "title_en",
  "title_ar",
  "statement_en",
  "statement_ar",
  "about_en",
  "about_ar",
  "email",
  "phone",
  "whatsapp",
  "telegram",
  "github_url",
  "linkedin_url",
  "upwork_url",
  "cv_url",
  "location_en",
  "location_ar",
  "availability_status",
  "hero_heading_en",
  "hero_heading_ar",
  "hero_subheading_en",
  "hero_subheading_ar",
  "hero_cta_en",
  "hero_cta_ar",
  "contact_cta_en",
  "contact_cta_ar",
  "profile_image_alt_en",
  "profile_image_alt_ar",
  "profile_image_position",
] as const;

export function buildProfilePatch(
  current: ProfileRecord,
  original: ProfileRecord,
): Record<string, string | null> {
  const patch: Record<string, string | null> = {};

  for (const field of editableProfileFields) {
    const value = current[field];
    if (value === original[field] || (typeof value !== "string" && value !== null)) continue;
    patch[field] = typeof value === "string" ? value.trim() : value;
  }

  return patch;
}
