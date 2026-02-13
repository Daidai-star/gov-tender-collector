from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session, require_admin
from app.core.config import get_settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.entities import Role, User
from app.schemas.auth import LoginRequest, TokenResponse, UserCreateRequest, UserOut

router = APIRouter()
settings = get_settings()


def _ensure_role(db: Session, role_name: str) -> Role:
    role = db.query(Role).filter(Role.name == role_name).first()
    if role:
        return role
    role = Role(name=role_name)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@router.post('/bootstrap', response_model=UserOut)
def bootstrap_admin(payload: UserCreateRequest, db: Session = Depends(get_db_session)):
    users_count = db.query(User).count()
    if users_count > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Bootstrap already finished')

    admin_role = _ensure_role(db, 'admin')
    user = User(username=payload.username, password_hash=get_password_hash(payload.password))
    user.roles.append(admin_role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut(id=user.id, username=user.username, roles=['admin'], created_at=user.created_at)


@router.post('/login', response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db_session)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Incorrect username or password')

    token = create_access_token(
        subject=user.username,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    return TokenResponse(access_token=token)


@router.post('/users', response_model=UserOut)
def create_user(
    payload: UserCreateRequest,
    db: Session = Depends(get_db_session),
    _: User = Depends(require_admin),
):
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='username already exists')

    role = _ensure_role(db, payload.role)
    user = User(username=payload.username, password_hash=get_password_hash(payload.password))
    user.roles.append(role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut(id=user.id, username=user.username, roles=[r.name for r in user.roles], created_at=user.created_at)


@router.get('/me', response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return UserOut(id=user.id, username=user.username, roles=[r.name for r in user.roles], created_at=user.created_at)


@router.get('/users', response_model=list[UserOut])
def list_users(db: Session = Depends(get_db_session), _: User = Depends(require_admin)):
    users = db.query(User).order_by(User.id.desc()).all()
    return [UserOut(id=user.id, username=user.username, roles=[r.name for r in user.roles], created_at=user.created_at) for user in users]
