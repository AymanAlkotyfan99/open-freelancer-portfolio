"use client";

import { Menu, Moon, Sun, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTheme } from "next-themes";
import { useState } from "react";

import { copy } from "@/lib/content";
import type { Locale } from "@/lib/types";
import { Button } from "./ui/button";

export function Header({ locale }: { locale: Locale }) {
  const c = copy[locale];
  const path = usePathname();
  const other = locale === "en" ? "ar" : "en";
  const { resolvedTheme, setTheme } = useTheme();
  const [open, setOpen] = useState(false);
  const translated = path.replace(/^\/(en|ar)/, `/${other}`);
  const links = [[c.home, ""], [c.about, "about"], [c.skills, "skills"], [c.projects, "projects"], [c.services, "services"], [c.experience, "experience"], [c.contact, "contact"]];
  return <header className="site-header"><div className="shell header-inner">
    <Link href={`/${locale}`} className="brand" aria-label={locale === "en" ? "Ayman Naeem home" : "الصفحة الرئيسية لأيمن نعيم"}><span>A/</span>Naeem</Link>
    <nav id="primary-navigation" className={`primary-nav ${open ? "open" : ""}`}>{links.map(([label, href]) => {
      const target = `/${locale}${href ? `/${href}` : ""}`;
      return <Link onClick={() => setOpen(false)} className="nav-link" aria-current={path === target ? "page" : undefined} key={href} href={target}>{label}</Link>;
    })}<Button asChild size="sm"><Link onClick={() => setOpen(false)} href={`/${locale}/request-project`}>{c.hire}</Link></Button></nav>
    <div className="header-actions"><Link className="icon-button language-switch" href={translated} hrefLang={other} aria-label={other === "ar" ? "العربية" : "English"}>{other}</Link><button className="icon-button" aria-label={locale === "en" ? "Toggle color theme" : "تبديل نمط الألوان"} onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}>{resolvedTheme === "light" ? <Moon size={17} /> : <Sun size={17} />}</button><button className="icon-button menu-button" aria-controls="primary-navigation" aria-expanded={open} aria-label={locale === "en" ? "Toggle navigation" : "فتح أو إغلاق التنقل"} onClick={() => setOpen(!open)}>{open ? <X /> : <Menu />}</button></div>
  </div></header>;
}

export function Footer({ locale }: { locale: Locale }) {
  return <footer className="site-footer"><div className="shell footer-grid"><div><Link href={`/${locale}`} className="brand"><span>A/</span>Naeem</Link><p>{locale === "en" ? "AI software engineering, automation, data, and full-stack delivery." : "هندسة برمجيات الذكاء الاصطناعي والأتمتة والبيانات والتطوير المتكامل."}</p></div><nav aria-label={locale === "en" ? "Footer navigation" : "تنقل التذييل"}><Link href={`/${locale}/projects`}>{copy[locale].projects}</Link><Link href={`/${locale}/services`}>{copy[locale].services}</Link><Link href={`/${locale}/contact`}>{copy[locale].contact}</Link><Link href={`/${locale}/privacy`}>{locale === "en" ? "Privacy" : "الخصوصية"}</Link></nav><p className="copyright">© {new Date().getFullYear()} Ayman Naeem.<br />{locale === "en" ? "Built for production." : "مصمم للإنتاج."}</p></div></footer>;
}
