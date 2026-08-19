"""Create deterministic browser-test data in the explicitly configured E2E database."""

import asyncio
from uuid import UUID

from app.database.session import SessionLocal, engine
from app.models.base import Base
from app.models.entities import (
    AdminUser,
    PackageFeatureValue,
    Profile,
    Project,
    ProjectTechnology,
    Service,
    ServiceFeature,
    ServicePackage,
)
from app.security.auth import hash_password


async def seed() -> None:
    if not str(engine.url).endswith("e2e.db"):
        raise RuntimeError("E2E seed refuses to modify a database not named e2e.db")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        db.add(
            Profile(
                id=UUID("10000000-0000-0000-0000-000000000001"),
                name_en="Ayman Naeem",
                name_ar="أيمن نعيم",
                title_en="AI Software Engineer & Full-Stack Developer",
                title_ar="مهندس برمجيات ذكاء اصطناعي ومطور متكامل",
                statement_en="Production-minded AI and web engineering.",
                statement_ar="هندسة ذكاء اصطناعي وويب بعقلية إنتاجية.",
                about_en="I build reliable software systems.",
                about_ar="أبني أنظمة برمجية موثوقة.",
                email="ayman@example.com",
            )
        )
        db.add(AdminUser(id=UUID("10000000-0000-0000-0000-000000000002"), email="admin@example.com", password_hash=hash_password("PortfolioE2E!123")))
        project = Project(
            id=UUID("20000000-0000-0000-0000-000000000001"),
            slug="e2e-no-media",
            title_en="E2E Project Without Media",
            title_ar="مشروع اختبار دون وسائط",
            summary_en="A published project deliberately created without images or optional links.",
            summary_ar="مشروع منشور أُنشئ عمداً دون صور أو روابط اختيارية.",
            content_en={},
            content_ar={},
            publication_status="published",
            ownership_type="personal",
        )
        db.add(project)
        await db.flush()
        db.add(ProjectTechnology(project_id=project.id, name="FastAPI", sort_order=0))

        service = Service(
            id=UUID("30000000-0000-0000-0000-000000000001"),
            slug="e2e-ai-service",
            title_en="E2E AI Service",
            title_ar="خدمة ذكاء اصطناعي للاختبار",
            description_en="A complete service used to validate packages and project requests.",
            description_ar="خدمة كاملة للتحقق من الباقات وطلبات المشاريع.",
            short_description_en="Reliable AI delivery with clear scope.",
            short_description_ar="تنفيذ موثوق للذكاء الاصطناعي بنطاق واضح.",
            related_skills=["FastAPI", "RAG"],
            included_items_en=["Architecture", "Source code"],
            included_items_ar=["المعمارية", "الشيفرة المصدرية"],
            publication_status="published",
            availability_status="available",
            is_featured=True,
        )
        db.add(service)
        await db.flush()
        basic = ServicePackage(
            id=UUID("40000000-0000-0000-0000-000000000001"),
            service_id=service.id,
            package_type="basic",
            name_en="Basic",
            name_ar="أساسية",
            price=250,
            currency="USD",
            delivery_days=5,
            revisions=1,
            included_deliverables_en=["API prototype"],
            included_deliverables_ar=["نموذج أولي للواجهة"],
            display_order=0,
        )
        standard = ServicePackage(
            id=UUID("40000000-0000-0000-0000-000000000002"),
            service_id=service.id,
            package_type="standard",
            name_en="Standard",
            name_ar="قياسية",
            price=425,
            currency="USD",
            delivery_days=10,
            revisions=2,
            included_deliverables_en=["Production API", "Documentation"],
            included_deliverables_ar=["واجهة إنتاجية", "توثيق"],
            is_recommended=True,
            display_order=1,
        )
        db.add_all([basic, standard])
        await db.flush()
        feature = ServiceFeature(
            id=UUID("50000000-0000-0000-0000-000000000001"),
            service_id=service.id,
            name_en="Deployment guide",
            name_ar="دليل النشر",
            value_type="boolean",
        )
        db.add(feature)
        await db.flush()
        db.add_all(
            [
                PackageFeatureValue(feature_id=feature.id, package_id=basic.id, value_boolean=False),
                PackageFeatureValue(feature_id=feature.id, package_id=standard.id, value_boolean=True),
            ]
        )
        await db.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
