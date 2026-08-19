export type Locale = "en" | "ar";

export type PageResult<T> = {
  items: T[];
  page: number;
  page_size: number;
  total: number;
  pages: number;
};

export type ProjectMedia = {
  id: string;
  media_type: "image" | "video";
  source_type: "upload" | "external_url";
  secure_url: string;
  thumbnail_url?: string | null;
  title_en?: string | null;
  title_ar?: string | null;
  alt_text_en?: string | null;
  alt_text_ar?: string | null;
  caption_en?: string | null;
  caption_ar?: string | null;
  is_cover: boolean;
  sort_order: number;
};

export type ProjectRecord = {
  id: string;
  slug: string;
  title_en: string;
  title_ar: string;
  summary_en: string;
  summary_ar: string;
  short_description_en?: string | null;
  short_description_ar?: string | null;
  category?: string | null;
  status_en?: string | null;
  status_ar?: string | null;
  cover_url?: string | null;
  github_url?: string | null;
  live_url?: string | null;
  demo_url?: string | null;
  project_date?: string | null;
  client_name?: string | null;
  role_en?: string | null;
  role_ar?: string | null;
  problem_en?: string | null;
  problem_ar?: string | null;
  solution_en?: string | null;
  solution_ar?: string | null;
  features_en?: string[];
  features_ar?: string[];
  architecture_en?: string | null;
  architecture_ar?: string | null;
  challenges_en?: string | null;
  challenges_ar?: string | null;
  implemented_solutions_en?: string | null;
  implemented_solutions_ar?: string | null;
  results_en?: string | null;
  results_ar?: string | null;
  team_members_en?: string | null;
  team_members_ar?: string | null;
  development_duration_en?: string | null;
  development_duration_ar?: string | null;
  ownership_type?: string | null;
  is_featured?: boolean;
  publication_status?: string;
  technologies: string[];
  media: ProjectMedia[];
};

export type ServicePackage = {
  id: string;
  service_id: string;
  package_type: "basic" | "standard" | "premium";
  name_en: string;
  name_ar: string;
  short_description_en?: string | null;
  short_description_ar?: string | null;
  price: string | number;
  currency: string;
  delivery_days: number;
  revisions?: number | null;
  unlimited_revisions: boolean;
  included_deliverables_en: string[];
  included_deliverables_ar: string[];
  excluded_items_en: string[];
  excluded_items_ar: string[];
  client_requirements_en: string[];
  client_requirements_ar: string[];
  is_active: boolean;
  is_recommended: boolean;
  display_order: number;
};

export type FeatureValue = {
  package_id: string;
  value_boolean?: boolean | null;
  value_number?: string | number | null;
  value_text_en?: string | null;
  value_text_ar?: string | null;
};

export type ServiceFeature = {
  id: string;
  name_en: string;
  name_ar: string;
  value_type: "boolean" | "number" | "text";
  values: FeatureValue[];
};

export type ServiceRecord = {
  id: string;
  slug: string;
  title_en: string;
  title_ar: string;
  description_en: string;
  description_ar: string;
  short_description_en?: string | null;
  short_description_ar?: string | null;
  cover_image_url?: string | null;
  introduction_video_url?: string | null;
  icon?: string;
  category?: string | null;
  related_skills: string[];
  scope_en?: string | null;
  scope_ar?: string | null;
  included_items_en: string[];
  included_items_ar: string[];
  excluded_items_en: string[];
  excluded_items_ar: string[];
  client_requirements_en: string[];
  client_requirements_ar: string[];
  is_featured: boolean;
  availability_status: string;
  publication_status: "draft" | "published" | "archived";
  packages: ServicePackage[];
  starting_price?: string | number | null;
  shortest_delivery_days?: number | null;
  comparison?: { packages: ServicePackage[]; features: ServiceFeature[] };
  faqs?: Array<{ id: string; question_en: string; question_ar: string; answer_en: string; answer_ar: string }>;
  related_projects?: ProjectRecord[];
};

export type ProfileRecord = Record<string, string | boolean | null | undefined> & {
  name_en?: string;
  name_ar?: string;
  title_en?: string;
  title_ar?: string;
  statement_en?: string;
  statement_ar?: string;
  about_en?: string;
  about_ar?: string;
  profile_image_url?: string | null;
  profile_image_alt_en?: string | null;
  profile_image_alt_ar?: string | null;
  profile_image_position?: string;
};
