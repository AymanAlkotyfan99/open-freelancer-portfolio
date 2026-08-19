"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { CheckCircle2, FileUp } from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { API_URL, api } from "@/lib/api";
import type { Locale, ServiceRecord } from "@/lib/types";
import { Turnstile } from "./turnstile";
import { Button } from "./ui/button";

const contactSchema = z.object({
  full_name: z.string().min(2), email: z.string().email(), subject: z.string().min(3),
  message: z.string().min(20), preferred_contact: z.enum(["email", "phone", "whatsapp", "telegram"]),
  consent: z.literal(true), website: z.string().optional(), turnstile_token: z.string().optional(),
});
const requestSchema = z.object({
  client_name: z.string().min(2), email: z.string().email(), company_name: z.string().optional(),
  phone: z.string().optional(), whatsapp: z.string().optional(), telegram: z.string().optional(),
  preferred_contact_method: z.enum(["email", "phone", "whatsapp", "telegram"]),
  service_id: z.string().optional(), package_id: z.string().optional(), project_title: z.string().min(3),
  project_description: z.string().min(20), expected_deliverables: z.string().optional(),
  preferred_start_date: z.string().optional(), consent: z.literal(true), website: z.string().optional(),
  turnstile_token: z.string().optional(),
});
type Contact = z.infer<typeof contactSchema>;
type RequestData = z.infer<typeof requestSchema>;

const labels = {
  en: { name: "Full name", email: "Email", subject: "Subject", message: "Message", method: "Preferred contact", consent: "I consent to being contacted about this inquiry.", send: "Send message", success: "Thanks—your message has been saved.", error: "Please review the form and try again." },
  ar: { name: "الاسم الكامل", email: "البريد الإلكتروني", subject: "الموضوع", message: "الرسالة", method: "طريقة التواصل المفضلة", consent: "أوافق على التواصل معي بخصوص هذا الطلب.", send: "إرسال الرسالة", success: "شكراً—تم حفظ رسالتك.", error: "راجع النموذج وحاول مجدداً." },
};

function Field({ label, error, ...props }: React.InputHTMLAttributes<HTMLInputElement> & { label: string; error?: string }) {
  return <label className="field"><span>{label}</span><input {...props} />{error && <small>{error}</small>}</label>;
}

export function ContactForm({ locale }: { locale: Locale }) {
  const l = labels[locale];
  const [notice, setNotice] = useState<{ ok: boolean; text: string } | null>(null);
  const { register, handleSubmit, formState: { errors, isSubmitting }, reset, setValue } = useForm<Contact>({ resolver: zodResolver(contactSchema), defaultValues: { preferred_contact: "email", website: "", turnstile_token: "" } });
  const submit = async (data: Contact) => {
    try { await api("/contact", { method: "POST", body: JSON.stringify(data) }); reset(); setNotice({ ok: true, text: l.success }); }
    catch { setNotice({ ok: false, text: l.error }); }
  };
  return <form className="form-card" onSubmit={handleSubmit(submit)} noValidate>
    <div className="grid gap-5 md:grid-cols-2"><Field label={l.name} {...register("full_name")} error={errors.full_name?.message} /><Field label={l.email} type="email" {...register("email")} error={errors.email?.message} /></div>
    <Field label={l.subject} {...register("subject")} error={errors.subject?.message} />
    <label className="field"><span>{l.message}</span><textarea rows={6} {...register("message")} />{errors.message && <small>{errors.message.message}</small>}</label>
    <label className="field"><span>{l.method}</span><select {...register("preferred_contact")}><option value="email">Email</option><option value="whatsapp">WhatsApp</option><option value="telegram">Telegram</option><option value="phone">Phone</option></select></label>
    <label className="checkbox"><input type="checkbox" {...register("consent")} /><span>{l.consent}</span></label>
    <input className="honeypot" tabIndex={-1} autoComplete="off" {...register("website")} />
    <Turnstile locale={locale} onToken={(token) => setValue("turnstile_token", token)} />
    <Button disabled={isSubmitting}>{isSubmitting ? (locale === "en" ? "Sending…" : "جارٍ الإرسال…") : l.send}</Button>
    {notice && <p role="status" className={notice.ok ? "form-success" : "form-error"}>{notice.ok && <CheckCircle2 size={18} />}{notice.text}</p>}
  </form>;
}

export function ProjectRequestForm({
  locale, services, selectedServiceId = "", selectedPackageId = "", referenceProjectId = "", custom = false,
}: { locale: Locale; services: ServiceRecord[]; selectedServiceId?: string; selectedPackageId?: string; referenceProjectId?: string; custom?: boolean }) {
  const l = labels[locale];
  const [notice, setNotice] = useState<{ ok: boolean; text: string } | null>(null);
  const [attachment, setAttachment] = useState<File | null>(null);
  const { register, handleSubmit, watch, setValue, formState: { errors, isSubmitting } } = useForm<RequestData>({
    resolver: zodResolver(requestSchema),
    defaultValues: { preferred_contact_method: "email", service_id: selectedServiceId, package_id: selectedPackageId, website: "", turnstile_token: "" },
  });
  const serviceId = watch("service_id");
  const service = services.find((item) => item.id === serviceId);
  const packages = service?.packages.filter((item) => item.is_active) ?? [];
  const packageId = watch("package_id");
  const selectedPackage = packages.find((item) => item.id === packageId);
  const isCustom = custom || !packageId;
  const serviceRegistration = register("service_id");
  useEffect(() => {
    const query = new URLSearchParams(window.location.search);
    setValue("service_id", selectedServiceId || query.get("service") || "");
    setValue("package_id", selectedPackageId || query.get("package") || "");
  }, [selectedPackageId, selectedServiceId, setValue]);
  const submit = async (data: RequestData) => {
    try {
      const output = await api<{ reference: string }>(isCustom ? "/custom-offer-requests" : "/project-requests", {
        method: "POST",
        body: JSON.stringify({
          ...data, service_id: data.service_id || null, package_id: isCustom ? null : data.package_id || null,
          displayed_price: selectedPackage?.price ?? null, currency: selectedPackage?.currency ?? null,
          delivery_days: selectedPackage?.delivery_days ?? null, reference_project_id: referenceProjectId || null,
          preferred_start_date: data.preferred_start_date || null,
        }),
      });
      if (attachment) {
        const body = new FormData(); body.append("file", attachment);
        const uploaded = await fetch(`${API_URL}/project-requests/${output.reference}/attachment`, { method: "POST", body, credentials: "include" });
        if (!uploaded.ok) throw new Error("Attachment upload failed");
      }
      setNotice({ ok: true, text: `${locale === "en" ? "Request saved. Reference" : "تم حفظ الطلب. المرجع"}: ${output.reference}` });
    } catch { setNotice({ ok: false, text: l.error }); }
  };
  return <form className="form-card" onSubmit={handleSubmit(submit)} noValidate>
    {selectedPackage && <div className="selected-package"><span>{locale === "en" ? "Selected package" : "الباقة المختارة"}</span><strong>{locale === "ar" ? selectedPackage.name_ar : selectedPackage.name_en}</strong><b>{selectedPackage.currency} {Number(selectedPackage.price).toLocaleString(locale)}</b><small>{locale === "en" ? "Final package data is verified securely when you submit." : "تُتحقق بيانات الباقة النهائية بأمان عند الإرسال."}</small></div>}
    <div className="grid gap-5 md:grid-cols-2"><Field label={l.name} {...register("client_name")} error={errors.client_name?.message} /><Field label={l.email} type="email" {...register("email")} error={errors.email?.message} /><Field label={locale === "en" ? "Company (optional)" : "الشركة (اختياري)"} {...register("company_name")} /><Field label={locale === "en" ? "Phone" : "الهاتف"} {...register("phone")} /><Field label="WhatsApp" {...register("whatsapp")} /><Field label="Telegram" {...register("telegram")} /></div>
    <div className="grid gap-5 md:grid-cols-2"><label className="field"><span>{locale === "en" ? "Service" : "الخدمة"}</span><select {...serviceRegistration} onChange={(event) => { serviceRegistration.onChange(event); setValue("package_id", ""); }}><option value="">{locale === "en" ? "General / custom work" : "عمل عام أو مخصص"}</option>{services.map((item) => <option key={item.id} value={item.id}>{locale === "ar" ? item.title_ar : item.title_en}</option>)}</select></label>
      {!custom && <label className="field"><span>{locale === "en" ? "Package" : "الباقة"}</span><select {...register("package_id")}><option value="">{locale === "en" ? "Custom offer" : "عرض مخصص"}</option>{packages.map((item) => <option value={item.id} key={item.id}>{locale === "ar" ? item.name_ar : item.name_en}</option>)}</select></label>}</div>
    <Field label={locale === "en" ? "Project title" : "عنوان المشروع"} {...register("project_title")} error={errors.project_title?.message} />
    <label className="field"><span>{locale === "en" ? "Detailed project description" : "وصف تفصيلي للمشروع"}</span><textarea rows={7} {...register("project_description")} />{errors.project_description && <small>{errors.project_description.message}</small>}</label>
    <label className="field"><span>{locale === "en" ? "Expected deliverables (optional)" : "المخرجات المتوقعة (اختياري)"}</span><textarea rows={3} {...register("expected_deliverables")} /></label>
    <div className="grid gap-5 md:grid-cols-2"><Field label={locale === "en" ? "Preferred start date" : "تاريخ البدء المفضل"} type="date" {...register("preferred_start_date")} /><label className="field"><span>{l.method}</span><select {...register("preferred_contact_method")}><option value="email">Email</option><option value="whatsapp">WhatsApp</option><option value="telegram">Telegram</option><option value="phone">Phone</option></select></label></div>
    <label className="upload-field"><FileUp /><span>{attachment ? attachment.name : locale === "en" ? "Attach a PDF, DOCX, PNG, or JPEG (optional)" : "أرفق PDF أو DOCX أو PNG أو JPEG (اختياري)"}</span><input type="file" accept=".pdf,.docx,.png,.jpg,.jpeg" onChange={(event) => setAttachment(event.target.files?.[0] ?? null)} /></label>
    <label className="checkbox"><input type="checkbox" {...register("consent")} /><span>{l.consent}</span></label>
    <input className="honeypot" tabIndex={-1} autoComplete="off" {...register("website")} />
    <Turnstile locale={locale} onToken={(token) => setValue("turnstile_token", token)} />
    <Button disabled={isSubmitting}>{isSubmitting ? (locale === "en" ? "Submitting…" : "جارٍ الإرسال…") : isCustom ? (locale === "en" ? "Request a custom offer" : "اطلب عرضاً مخصصاً") : (locale === "en" ? "Submit package request" : "إرسال طلب الباقة")}</Button>
    {notice && <p role="status" className={notice.ok ? "form-success" : "form-error"}>{notice.ok && <CheckCircle2 size={18} />}{notice.text}</p>}
  </form>;
}
