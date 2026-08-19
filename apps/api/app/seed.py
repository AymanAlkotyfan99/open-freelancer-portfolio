import asyncio

from sqlalchemy import select

from app.database.session import SessionLocal
from app.models.entities import (
    Activity,
    Education,
    Experience,
    Profile,
    Project,
    Service,
    SiteSetting,
    Skill,
    SkillCategory,
    SocialLink,
)

PROJECTS = [
    (
        "biavora-platform",
        "BIAVORA Platform",
        "منصة BIAVORA",
        "AI",
        "Graduation Project / Startup-Oriented Platform",
        "An AI-agent-powered business intelligence platform that transforms voice or text questions into SQL queries, dashboards, KPIs, and forecasting insights.",
        [
            "Whisper",
            "sqlglot",
            "ClickHouse",
            "PostgreSQL",
            "TimesFM",
            "React",
            "Python",
            "LLM APIs",
        ],
    ),
    (
        "wassal-platform",
        "Wassal Platform",
        "منصة Wassal",
        "Full-Stack",
        "In Development",
        "A Syrian e-commerce and affiliate marketing platform connecting suppliers, marketers, and customers, with COD, product, order, and commission management.",
        ["React", "TypeScript", "Fastify", "Prisma", "PostgreSQL", "BullMQ", "Docker"],
    ),
    (
        "netrexon",
        "NetReXon",
        "NetReXon",
        "Full-Stack",
        "Portfolio Project",
        "A platform for presenting and managing products, datasheets, images, PDF files, orders, and contact messages, including an administration dashboard.",
        ["React", "PostgreSQL", "REST API"],
    ),
    (
        "financial-management-systems",
        "Financial Management Systems",
        "أنظمة الإدارة المالية",
        "Backend",
        "Client Work",
        "Financial management systems delivered for clients, including account, transaction, and financial reporting management. Confidential client information is excluded.",
        ["Backend Engineering", "SQL", "Reporting"],
    ),
    (
        "gaza-virtual-reconstruction",
        "Gaza Virtual Reconstruction Using Pix2Pix",
        "إعادة الإعمار الافتراضية لغزة",
        "Computer Vision",
        "Research Project",
        "A deep-learning virtual reconstruction project using Sentinel-2 L2A satellite imagery and Pix2Pix with U-Net and PatchGAN.",
        ["PyTorch", "Pix2Pix", "U-Net", "PatchGAN", "MAE: 0.1388", "PSNR: 15.32 dB", "SSIM: 0.425"],
    ),
    (
        "driver-distraction-classification",
        "Driver Distraction Classification",
        "تصنيف تشتت السائق",
        "Computer Vision",
        "Machine Learning Project",
        "A computer vision system for classifying driver distraction using CNN and MobileNetV2.",
        ["CNN", "MobileNetV2", "Computer Vision"],
    ),
    (
        "medical-imaging-brain-segmentation",
        "Medical Imaging and Brain Segmentation",
        "التصوير الطبي وتقسيم الدماغ",
        "Computer Vision",
        "Academic Activity",
        "Medical image analysis and brain segmentation work, including participation in the RISE-MICCAI Summer School and Challenge.",
        ["Medical Imaging", "Segmentation", "Deep Learning"],
    ),
    (
        "smart-parking-management",
        "Smart Parking Management System",
        "نظام إدارة مواقف ذكي",
        "Desktop Applications",
        "Completed",
        "A Java Swing desktop application for managing parking slots, registered vehicles, operations, and Java Serialization-based persistence.",
        ["Java", "Swing", "Serialization"],
    ),
]
SERVICES = [
    ("AI Agents and Automation", "وكلاء الذكاء الاصطناعي والأتمتة", "AI Agents"),
    ("RAG Knowledge Assistants", "مساعدو المعرفة بتقنية RAG", "RAG"),
    ("AI Chatbots and Virtual Assistants", "روبوتات المحادثة والمساعدون الافتراضيون", "LLM APIs"),
    ("LLM and API Integration", "تكامل نماذج اللغة وواجهات API", "LLM APIs"),
    ("Full-Stack Web Application Development", "تطوير تطبيقات ويب متكاملة", "Next.js"),
    ("Backend and REST API Development", "تطوير الأنظمة الخلفية وواجهات REST", "FastAPI"),
    ("SaaS Application Development", "تطوير تطبيقات SaaS", "PostgreSQL"),
    ("Business Intelligence Dashboards", "لوحات ذكاء الأعمال", "Metabase"),
    ("Data Processing and ETL Pipelines", "معالجة البيانات وخطوط ETL", "ETL"),
    ("Machine Learning Solutions", "حلول تعلم الآلة", "Machine Learning"),
    ("Computer Vision Solutions", "حلول الرؤية الحاسوبية", "Computer Vision"),
    ("Database Design and Integration", "تصميم قواعد البيانات وتكاملها", "PostgreSQL"),
    ("Dockerization and Application Deployment", "حاويات Docker ونشر التطبيقات", "Docker"),
    ("Third-Party API, OAuth, and Webhook Integration", "تكامل API وOAuth وWebhooks", "OAuth"),
    ("AI-Powered Internal Tools", "أدوات داخلية مدعومة بالذكاء الاصطناعي", "AI Agents"),
    ("Admin Dashboards and Management Systems", "لوحات الإدارة وأنظمة التحكم", "React"),
]
SKILLS = {
    "Languages": ["Python", "JavaScript", "TypeScript", "SQL", "Java", "C++", "C"],
    "Frontend": ["React", "Next.js", "Tailwind CSS", "shadcn/ui", "TanStack Query", "Zustand"],
    "Backend and APIs": [
        "FastAPI",
        "Django",
        "Flask",
        "Node.js",
        "Fastify",
        "REST APIs",
        "Webhooks",
        "OAuth",
    ],
    "Databases and Data": [
        "PostgreSQL",
        "MySQL",
        "SQLite",
        "ClickHouse",
        "SurrealDB",
        "Prisma ORM",
        "ETL",
    ],
    "AI and Machine Learning": [
        "LLM APIs",
        "AI Agents",
        "Agentic Workflows",
        "RAG",
        "LangChain",
        "LangGraph",
        "Whisper Speech-to-Text",
        "TimesFM",
        "PyTorch",
        "Machine Learning",
        "Computer Vision",
        "NLP",
        "Pix2Pix",
        "U-Net",
        "OCR",
    ],
    "Infrastructure and Tools": [
        "Docker",
        "Docker Compose",
        "Git",
        "GitHub Actions",
        "Linux",
        "Nginx",
        "Metabase",
    ],
}


async def run_seed() -> None:
    async with SessionLocal() as db:
        if not await db.scalar(select(Profile)):
            db.add(
                Profile(
                    name_en="Ayman Naeem",
                    name_ar="أيمن نعيم",
                    title_en="AI Software Engineer & Full-Stack Developer",
                    title_ar="مهندس برمجيات ذكاء اصطناعي ومطور متكامل",
                    statement_en="I build production-ready AI systems, intelligent automation workflows, scalable backend services, and modern full-stack web applications.",
                    statement_ar="أبني أنظمة ذكاء اصطناعي جاهزة للإنتاج، وحلول أتمتة ذكية، وخدمات خلفية قابلة للتوسع، وتطبيقات ويب متكاملة وحديثة.",
                    about_en="Production-minded engineering across AI, backend, data, and full-stack systems.",
                    about_ar="هندسة بعقلية إنتاجية عبر الذكاء الاصطناعي والخلفية والبيانات والتطوير المتكامل.",
                )
            )
        for order, (category, names) in enumerate(SKILLS.items()):
            row = await db.scalar(select(SkillCategory).where(SkillCategory.name_en == category))
            if not row:
                row = SkillCategory(
                    name_en=category,
                    name_ar=category,
                    slug=category.lower().replace(" ", "-").replace("and-", ""),
                    sort_order=order,
                )
                db.add(row)
                await db.flush()
                for i, name in enumerate(names):
                    db.add(
                        Skill(
                            category_id=row.id,
                            name=name,
                            priority=100 - i,
                            sort_order=i,
                            is_featured=i < 4,
                        )
                    )
        for i, p in enumerate(PROJECTS):
            if not await db.scalar(select(Project).where(Project.slug == p[0])):
                db.add(
                    Project(
                        slug=p[0],
                        title_en=p[1],
                        title_ar=p[2],
                        category=p[3],
                        status_en=p[4],
                        status_ar=p[4],
                        summary_en=p[5],
                        summary_ar=p[5],
                        content_en={"technologies": p[6]},
                        content_ar={"technologies": p[6]},
                        sort_order=i,
                        is_featured=i < 4,
                    )
                )
        for i, (title, title_ar, related_skill) in enumerate(SERVICES):
            slug = title.lower().replace(" ", "-").replace("&", "and")
            if not await db.scalar(select(Service).where(Service.slug == slug)):
                db.add(
                    Service(
                        slug=slug,
                        title_en=title,
                        title_ar=title_ar,
                        description_en="Draft service description. Configure scope and commercial details before publishing.",
                        description_ar="وصف مسودة للخدمة. اضبط النطاق والتفاصيل التجارية قبل النشر.",
                        related_skills=[related_skill],
                        technologies=[],
                        deliverables_en=[],
                        deliverables_ar=[],
                        sort_order=i,
                        is_featured=i < 4,
                        publication_status="draft",
                    )
                )
        if not await db.scalar(select(Experience)):
            db.add(
                Experience(
                    title_en="Freelance Full-Stack Software Engineer and AI Integration",
                    title_ar="مهندس برمجيات متكامل مستقل وتكامل الذكاء الاصطناعي",
                    description_en="Delivered financial systems, web applications, and AI tools for clients.",
                    description_ar="قدمت أنظمة مالية وتطبيقات ويب وأدوات ذكاء اصطناعي للعملاء.",
                )
            )
        if not await db.scalar(select(Education)):
            db.add(
                Education(
                    title_en="Final-Year Informatics Engineering Student",
                    title_ar="طالب هندسة معلوماتية في السنة النهائية",
                    description_en="Software Engineering specialization.",
                    description_ar="اختصاص هندسة البرمجيات.",
                    institution_en="Syrian Private University",
                    institution_ar="الجامعة السورية الخاصة",
                )
            )
        if not await db.scalar(select(Activity)):
            db.add(
                Activity(
                    title_en="RISE-MICCAI Summer School and Brain Segmentation Challenge",
                    title_ar="مدرسة RISE-MICCAI وتحدي تقسيم الدماغ",
                    description_en="Participation in medical imaging learning and challenge activities.",
                    description_ar="مشاركة في أنشطة تعلم وتحدي التصوير الطبي.",
                )
            )
        for i, (platform, url) in enumerate(
            {
                "GitHub": "[GITHUB_URL]",
                "LinkedIn": "[LINKEDIN_URL]",
                "Upwork": "[UPWORK_URL]",
                "WhatsApp": "[WHATSAPP]",
                "Telegram": "[TELEGRAM]",
            }.items()
        ):
            if not await db.scalar(select(SocialLink).where(SocialLink.platform == platform)):
                db.add(SocialLink(platform=platform, url=url, icon=platform, sort_order=i))
        if not await db.scalar(select(SiteSetting).where(SiteSetting.key == "github_allowlist")):
            db.add(SiteSetting(key="github_allowlist", value={"repositories": []}, is_public=False))
        await db.commit()
        print("Portfolio seed data is ready.")


def seed() -> None:
    asyncio.run(run_seed())
