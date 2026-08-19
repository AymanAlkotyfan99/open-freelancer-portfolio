import asyncio
import getpass

from email_validator import validate_email
from sqlalchemy import select

from app.database.session import SessionLocal
from app.models.entities import AdminUser
from app.security.auth import hash_password


async def _create_admin(email: str, password: str) -> None:
    async with SessionLocal() as db:
        if await db.scalar(select(AdminUser).where(AdminUser.email == email)):
            raise SystemExit("An administrator with that email already exists")
        db.add(AdminUser(email=email, password_hash=hash_password(password)))
        await db.commit()
        print("Administrator created securely.")


def create_admin() -> None:
    email = validate_email(
        input("Admin email: ").strip(), check_deliverability=False
    ).normalized.lower()
    password = getpass.getpass("Password (12+ characters): ")
    if len(password) < 12 or password != getpass.getpass("Confirm password: "):
        raise SystemExit("Passwords must match and contain at least 12 characters")
    asyncio.run(_create_admin(email, password))
