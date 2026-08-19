import { notFound } from "next/navigation";
import { Footer, Header } from "@/components/site";
import type { Locale } from "@/lib/content";
export function generateStaticParams() { return [{ locale: "en" }, { locale: "ar" }]; }
export default async function LocaleLayout({ children, params }: { children: React.ReactNode; params: Promise<{locale:string}> }) { const { locale } = await params; if (!['en','ar'].includes(locale)) notFound(); return <div dir={locale === 'ar' ? 'rtl' : 'ltr'} lang={locale}><Header locale={locale as Locale}/>{children}<Footer locale={locale as Locale}/></div> }

