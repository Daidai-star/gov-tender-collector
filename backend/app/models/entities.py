import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class RoleType(str, enum.Enum):
    admin = 'admin'
    user = 'user'


class CrawlJobStatus(str, enum.Enum):
    queued = 'queued'
    running = 'running'
    completed = 'completed'
    failed = 'failed'


class NoticeStatus(str, enum.Enum):
    active = 'active'
    archived = 'archived'


class AIJobStatus(str, enum.Enum):
    pending = 'pending'
    running = 'running'
    done = 'done'
    failed = 'failed'


user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    roles = relationship('Role', secondary=user_roles, back_populates='users')
    favorites = relationship('FavoriteNotice', back_populates='user', cascade='all,delete-orphan')


class Role(Base):
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True)
    name = Column(String(32), unique=True, nullable=False, index=True)

    users = relationship('User', secondary=user_roles, back_populates='roles')


class Site(Base):
    __tablename__ = 'sites'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    base_url = Column(String(512), nullable=False)
    province = Column(String(64), nullable=False)
    city = Column(String(64), nullable=False)
    adapter_key = Column(String(64), nullable=False, default='generic_html')
    crawl_enabled = Column(Boolean, default=True, nullable=False)
    rate_limit = Column(Integer, default=4, nullable=False)
    schedule_group = Column(String(64), default='default', nullable=False)
    parser_rules = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)


class CrawlJob(Base):
    __tablename__ = 'crawl_jobs'

    id = Column(Integer, primary_key=True, index=True)
    status = Column(Enum(CrawlJobStatus), default=CrawlJobStatus.queued, nullable=False)
    trigger_type = Column(String(32), default='manual', nullable=False)
    filters = Column(JSON, default=dict, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    metrics = Column(JSON, default=dict, nullable=False)
    error_message = Column(Text, nullable=True)

    logs = relationship('CrawlJobLog', back_populates='job', cascade='all,delete-orphan')


class CrawlJobLog(Base):
    __tablename__ = 'crawl_job_logs'

    id = Column(Integer, primary_key=True)
    crawl_job_id = Column(Integer, ForeignKey('crawl_jobs.id', ondelete='CASCADE'), nullable=False, index=True)
    level = Column(String(16), default='INFO', nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    job = relationship('CrawlJob', back_populates='logs')


class Notice(Base):
    __tablename__ = 'notices'
    __table_args__ = (
        UniqueConstraint('source_url_hash', name='uq_notices_source_url_hash'),
        Index('idx_notices_publish_time', 'publish_time'),
        Index('idx_notices_tender_type', 'tender_type'),
        Index('idx_notices_region', 'region_province', 'region_city'),
        Index('idx_notices_content_tsv', text("to_tsvector('simple', coalesce(content_text,''))"), postgresql_using='gin'),
    )

    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey('sites.id', ondelete='SET NULL'), nullable=True)
    title = Column(String(500), nullable=False)
    source_url = Column(String(1000), nullable=False)
    source_url_hash = Column(String(64), nullable=False)
    source_notice_id = Column(String(128), nullable=True)
    publish_time = Column(DateTime, nullable=True)
    tender_type = Column(String(64), nullable=False)
    region_province = Column(String(64), nullable=False)
    region_city = Column(String(64), nullable=False)
    content_text = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False, index=True)
    has_attachments = Column(Boolean, default=False, nullable=False)
    status = Column(Enum(NoticeStatus), default=NoticeStatus.active, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    site = relationship('Site')
    attachments = relationship('Attachment', back_populates='notice', cascade='all,delete-orphan')
    versions = relationship('NoticeVersion', back_populates='notice', cascade='all,delete-orphan')
    ai_records = relationship('AIAnalysisRecord', back_populates='notice', cascade='all,delete-orphan')
    favorites = relationship('FavoriteNotice', back_populates='notice', cascade='all,delete-orphan')


class NoticeVersion(Base):
    __tablename__ = 'notice_versions'

    id = Column(Integer, primary_key=True)
    notice_id = Column(Integer, ForeignKey('notices.id', ondelete='CASCADE'), nullable=False)
    content_hash = Column(String(64), nullable=False)
    content_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    notice = relationship('Notice', back_populates='versions')


class Attachment(Base):
    __tablename__ = 'attachments'

    id = Column(Integer, primary_key=True)
    notice_id = Column(Integer, ForeignKey('notices.id', ondelete='CASCADE'), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(32), nullable=False)
    file_size = Column(Integer, nullable=False)
    storage_path = Column(String(1024), nullable=False)
    sha256 = Column(String(64), nullable=False)
    source_url = Column(String(1000), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    notice = relationship('Notice', back_populates='attachments')


class AIAnalysisRecord(Base):
    __tablename__ = 'ai_analysis_records'

    id = Column(Integer, primary_key=True)
    notice_id = Column(Integer, ForeignKey('notices.id', ondelete='CASCADE'), nullable=False, index=True)
    model = Column(String(120), nullable=False)
    status = Column(Enum(AIJobStatus), default=AIJobStatus.pending, nullable=False)
    summary = Column(Text, nullable=True)
    key_requirements = Column(JSON, default=list, nullable=False)
    risk_points = Column(JSON, default=list, nullable=False)
    deadline_items = Column(JSON, default=list, nullable=False)
    raw_json = Column(JSON, default=dict, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    notice = relationship('Notice', back_populates='ai_records')


class FavoriteNotice(Base):
    __tablename__ = 'favorite_notices'
    __table_args__ = (
        UniqueConstraint('user_id', 'notice_id', name='uq_favorite_user_notice'),
        Index('idx_favorite_user', 'user_id'),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    notice_id = Column(Integer, ForeignKey('notices.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    user = relationship('User', back_populates='favorites')
    notice = relationship('Notice', back_populates='favorites')


def utc_now() -> datetime:
    return datetime.utcnow()
