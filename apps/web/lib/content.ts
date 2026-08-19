export type Locale = "en" | "ar";
export type Project = { slug: string; title: string; category: string; status: string; summary: string; tech: string[]; metrics?: string[] };

const projectsEn: Project[] = [
  { slug: "biavora-platform", title: "BIAVORA Platform", category: "AI", status: "Graduation Project · Startup-Oriented", summary: "An AI-agent-powered business intelligence platform that turns voice or text questions into SQL, dashboards, KPIs, and forecasting insights.", tech: ["Whisper", "LLM APIs", "sqlglot", "ClickHouse", "PostgreSQL", "TimesFM", "React", "Docker"] },
  { slug: "wassal-platform", title: "Wassal Platform", category: "Full-Stack", status: "In Development", summary: "A Syrian e-commerce and affiliate platform connecting suppliers, marketers, and customers with COD, order, and commission management.", tech: ["React", "TypeScript", "Fastify", "Prisma", "PostgreSQL", "BullMQ", "Docker"] },
  { slug: "netrexon", title: "NetReXon", category: "Full-Stack", status: "Completed", summary: "A product and order management platform for datasheets, imagery, PDF files, inquiries, and administration.", tech: ["React", "REST API", "PostgreSQL"] },
  { slug: "financial-management-systems", title: "Financial Management Systems", category: "Backend", status: "Client Work", summary: "Confidential financial systems covering accounts, transactions, and financial reporting without exposing client data.", tech: ["Backend Engineering", "SQL", "Reporting"] },
  { slug: "gaza-virtual-reconstruction", title: "Gaza Virtual Reconstruction", category: "Computer Vision", status: "Research Project", summary: "Deep-learning virtual reconstruction from Sentinel-2 L2A satellite imagery using Pix2Pix with U-Net and PatchGAN.", tech: ["PyTorch", "Pix2Pix", "U-Net", "PatchGAN", "Sentinel-2"], metrics: ["MAE 0.1388", "PSNR 15.32 dB", "SSIM 0.425"] },
  { slug: "driver-distraction-classification", title: "Driver Distraction Classification", category: "Computer Vision", status: "Machine Learning Project", summary: "A computer vision system for classifying driver distraction using CNN and MobileNetV2.", tech: ["Python", "CNN", "MobileNetV2", "Computer Vision"] },
  { slug: "medical-imaging-brain-segmentation", title: "Medical Imaging & Brain Segmentation", category: "Computer Vision", status: "Academic Activity", summary: "Medical image analysis and brain segmentation work connected to the RISE-MICCAI Summer School and Challenge.", tech: ["Medical Imaging", "Segmentation", "Deep Learning"] },
  { slug: "smart-parking", title: "Smart Parking Management System", category: "Desktop Applications", status: "Completed", summary: "A Java Swing desktop application for parking slots, registered vehicles, operations, and serialization-based persistence.", tech: ["Java", "Swing", "Serialization"] }
];

const arText: Record<string, [string, string]> = {
  "biavora-platform": ["منصة BIAVORA", "منصة ذكاء أعمال مدعومة بوكلاء الذكاء الاصطناعي تحوّل الأسئلة الصوتية أو النصية إلى SQL ولوحات مؤشرات وتنبؤات."],
  "wassal-platform": ["منصة Wassal", "منصة سورية للتجارة الإلكترونية والتسويق بالعمولة تربط الموردين والمسوقين والعملاء مع إدارة الدفع عند الاستلام والطلبات والعمولات."],
  "netrexon": ["NetReXon", "منصة لإدارة وعرض المنتجات وملفات البيانات والصور وملفات PDF والطلبات والرسائل مع لوحة إدارة."],
  "financial-management-systems": ["أنظمة الإدارة المالية", "أنظمة مالية للعملاء تشمل الحسابات والمعاملات والتقارير دون كشف بيانات سرية."],
  "gaza-virtual-reconstruction": ["إعادة الإعمار الافتراضية لغزة", "مشروع تعلم عميق لإعادة الإعمار من صور Sentinel-2 باستخدام Pix2Pix وU-Net وPatchGAN."],
  "driver-distraction-classification": ["تصنيف تشتت السائق", "نظام رؤية حاسوبية لتصنيف تشتت السائق باستخدام CNN وMobileNetV2."],
  "medical-imaging-brain-segmentation": ["التصوير الطبي وتقسيم الدماغ", "عمل في تحليل الصور الطبية وتقسيم الدماغ مرتبط بمدرسة وتحدي RISE-MICCAI."],
  "smart-parking": ["نظام إدارة مواقف ذكي", "تطبيق مكتبي بـ Java Swing لإدارة المواقف والمركبات والعمليات والتخزين بالتسلسل."]
};

export const projects = (locale: Locale): Project[] => locale === "en" ? projectsEn : projectsEn.map(p => ({ ...p, title: arText[p.slug][0], summary: arText[p.slug][1] }));
export const skillGroups = [
  ["AI & Machine Learning", ["LLM APIs", "AI Agents", "Agentic Workflows", "RAG", "LangChain", "LangGraph", "PyTorch", "Computer Vision", "NLP", "OCR"]],
  ["Backend & APIs", ["FastAPI", "Django", "Flask", "Node.js", "Fastify", "REST APIs", "Webhooks", "OAuth"]],
  ["Frontend", ["React", "Next.js", "TypeScript", "Tailwind CSS", "shadcn/ui", "TanStack Query", "Zustand"]],
  ["Data", ["PostgreSQL", "MySQL", "ClickHouse", "SurrealDB", "Prisma", "SQL", "ETL", "Metabase"]],
  ["Infrastructure", ["Docker", "GitHub Actions", "Linux", "Nginx", "Git", "Cloud Deployment"]],
  ["Languages", ["Python", "JavaScript", "TypeScript", "SQL", "Java", "C++", "C"]]
] as const;
export const services = ["AI Agents & Automation", "RAG Systems", "LLM Integration", "Full-Stack Web Development", "Backend & REST APIs", "Business Intelligence", "Data Processing & ETL", "Machine Learning & Computer Vision", "Third-Party Integrations", "Dockerization & Deployment"];

export const copy = {
  en: { home: "Home", about: "About", skills: "Skills", projects: "Projects", services: "Services", experience: "Experience", contact: "Contact", hire: "Hire me", title: "AI Software Engineer & Full-Stack Developer", statement: "I build production-ready AI systems, intelligent automation workflows, scalable backend services, and modern full-stack web applications.", available: "Available for remote opportunities and freelance projects.", work: "View my work", request: "Request a project", cv: "Download CV", intro: "Engineering beyond the prototype", summary: "I design the systems behind intelligent products—from LLM orchestration and reliable APIs to data pipelines, user experiences, and deployment. The focus is software that survives real users, real data, and production constraints.", selected: "Selected work", capabilities: "Core capabilities", discuss: "Have a system worth building?", discussText: "Bring the problem. I’ll help shape a practical path from architecture to production.", allProjects: "Explore all projects" },
  ar: { home: "الرئيسية", about: "عني", skills: "المهارات", projects: "المشاريع", services: "الخدمات", experience: "الخبرة", contact: "تواصل", hire: "وظّفني", title: "مهندس برمجيات ذكاء اصطناعي ومطور متكامل", statement: "أبني أنظمة ذكاء اصطناعي جاهزة للإنتاج، وحلول أتمتة ذكية، وخدمات خلفية قابلة للتوسع، وتطبيقات ويب متكاملة وحديثة.", available: "متاح للفرص عن بُعد والمشاريع المستقلة.", work: "شاهد أعمالي", request: "اطلب مشروعاً", cv: "تحميل السيرة", intro: "هندسة تتجاوز النموذج الأولي", summary: "أصمم الأنظمة خلف المنتجات الذكية، من تنسيق نماذج اللغة وواجهات API الموثوقة إلى خطوط البيانات وتجربة المستخدم والنشر، مع التركيز على برمجيات تتحمل واقع الإنتاج.", selected: "أعمال مختارة", capabilities: "القدرات الأساسية", discuss: "هل لديك نظام يستحق البناء؟", discussText: "شارك المشكلة، وسأساعدك في صياغة مسار عملي من المعمارية إلى الإنتاج.", allProjects: "استكشف كل المشاريع" }
};

