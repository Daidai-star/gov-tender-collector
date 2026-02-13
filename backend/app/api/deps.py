from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models.entities import User

settings = get_settings()
security = HTTPBearer(auto_error=True)


def get_db_session() -> Generator[Session, None, None]:
    yield from get_db()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db_session),
) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=['HS256'])
        subject = payload.get('sub')
        if not subject:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token')
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token') from exc

    user = db.query(User).filter(User.username == subject).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found')
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not any(role.name == 'admin' for role in user.roles):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Admin role required')
    return user
