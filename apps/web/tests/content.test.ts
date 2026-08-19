import { describe, expect, it } from "vitest";
import { projects } from "@/lib/content";
describe('localized content',()=>{it('includes eight case studies in both languages',()=>{expect(projects('en')).toHaveLength(8);expect(projects('ar')).toHaveLength(8)});it('does not invent project links',()=>{expect(JSON.stringify(projects('en'))).not.toContain('github.com')})});

