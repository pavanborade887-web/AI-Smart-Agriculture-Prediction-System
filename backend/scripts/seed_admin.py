"""Create or update an administrator from environment variables.

Set ADMIN_EMAIL, ADMIN_PASSWORD, and optionally ADMIN_NAME before running.
"""
import os
from sqlalchemy import select
from app.core.security import hash_password
from app.db import Base, SessionLocal, engine
from app.models import Role, User


def main() -> None:
    email = os.environ.get("ADMIN_EMAIL", "").lower().strip()
    password = os.environ.get("ADMIN_PASSWORD", "")
    name = os.environ.get("ADMIN_NAME", "Platform Administrator").strip()
    if not email or len(password) < 8:
        raise SystemExit("Set ADMIN_EMAIL and an ADMIN_PASSWORD with at least 8 characters.")
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        if user:
            user.full_name, user.password_hash, user.role, user.is_active = name, hash_password(password), Role.admin, True
        else:
            db.add(User(full_name=name, email=email, password_hash=hash_password(password), role=Role.admin))
        db.commit()
    print(f"Administrator ready: {email}")


if __name__ == "__main__":
    main()
