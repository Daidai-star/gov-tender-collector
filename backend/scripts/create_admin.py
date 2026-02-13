from app.core.database import SessionLocal
from app.core.init_db import ensure_seed_roles_and_admin, init_db


def main():
    init_db()
    db = SessionLocal()
    try:
        ensure_seed_roles_and_admin(db, 'admin', 'admin123456')
        print('admin seeded: admin / admin123456')
    finally:
        db.close()


if __name__ == '__main__':
    main()
