"""Create (or promote) an administrator account (pengelola).

Admins cannot be created through the public API, so use this script once to
provision one for local use:

    python -m app.scripts.create_admin <username> <email> <password>

If the username already exists, it is promoted to the admin role instead.
"""

import asyncio
import sys

from app.core.database import AsyncSessionLocal, Base, engine
from app.core.security import hash_password
from app.crud import user as user_crud
from app.models.enums import UserRole
from app.models.user import User


async def _run(username: str, email: str, password: str) -> None:
    # Make sure the tables exist (handy on the zero-setup SQLite default).
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        existing = await user_crud.get_user_by_username(db, username)
        if existing is not None:
            existing.role = UserRole.ADMIN.value
            existing.is_verified = True
            await db.commit()
            print(f"✓ Pengguna '{username}' dipromosikan menjadi pengelola (admin).")
            return
        admin = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            role=UserRole.ADMIN.value,
            is_verified=True,
        )
        db.add(admin)
        await db.commit()
        print(f"✓ Akun pengelola '{username}' berhasil dibuat.")


def main() -> None:
    if len(sys.argv) != 4:
        print("Usage: python -m app.scripts.create_admin <username> <email> <password>")
        raise SystemExit(1)
    _, username, email, password = sys.argv
    asyncio.run(_run(username, email, password))


if __name__ == "__main__":
    main()
