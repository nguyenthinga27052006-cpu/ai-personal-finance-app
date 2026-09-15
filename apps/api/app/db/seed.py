from sqlalchemy.orm import Session

from app.auth.security import hash_password
from app.db.models import User, UserRole, UserStatus
from app.db.models.finance import seed_system_categories as _seed_system_categories


def seed_system_categories(session: Session) -> None:
    _seed_system_categories(session)


def seed_super_admin(session: Session) -> User:
    admin = session.query(User).filter(User.email == "admin@finance.app").first()
    if not admin:
        admin = User(
            email="admin@finance.app",
            password_hash=hash_password("AdminPass123!"),
            display_name="Super Admin",
            role=UserRole.ADMIN.value,
            status=UserStatus.ACTIVE.value,
        )
        session.add(admin)
    else:
        admin.password_hash = hash_password("AdminPass123!")
        admin.role = UserRole.ADMIN.value
        admin.status = UserStatus.ACTIVE.value
    session.commit()
    session.refresh(admin)
    return admin

