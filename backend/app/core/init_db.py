from sqlalchemy.orm import Session

from app.core.database import Base, engine
from app.core.security import get_password_hash
from app.models.entities import Role, User


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def ensure_seed_roles_and_admin(db: Session, username: str, password: str) -> None:
    admin_role = db.query(Role).filter(Role.name == 'admin').first()
    user_role = db.query(Role).filter(Role.name == 'user').first()

    if not admin_role:
        admin_role = Role(name='admin')
        db.add(admin_role)
    if not user_role:
        user_role = Role(name='user')
        db.add(user_role)
    db.commit()

    if db.query(User).count() == 0:
        admin = User(username=username, password_hash=get_password_hash(password))
        admin.roles.append(admin_role)
        db.add(admin)
        db.commit()
