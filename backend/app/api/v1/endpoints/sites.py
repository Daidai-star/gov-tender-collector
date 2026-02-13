from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, require_admin
from app.models.entities import Site, User
from app.schemas.site import SiteCreateRequest, SiteOut, SiteUpdateRequest
from app.services.crawler.presets import HENAN_SEED_SITES

router = APIRouter()


@router.get('', response_model=list[SiteOut])
def list_sites(db: Session = Depends(get_db_session), _: User = Depends(require_admin)):
    sites = db.query(Site).order_by(Site.id.desc()).all()
    return sites


@router.post('', response_model=SiteOut)
def create_site(
    payload: SiteCreateRequest,
    db: Session = Depends(get_db_session),
    _: User = Depends(require_admin),
):
    site = Site(
        name=payload.name,
        base_url=str(payload.base_url),
        province=payload.province,
        city=payload.city,
        adapter_key=payload.adapter_key,
        crawl_enabled=payload.crawl_enabled,
        rate_limit=payload.rate_limit,
        schedule_group=payload.schedule_group,
        parser_rules=payload.parser_rules,
    )
    db.add(site)
    db.commit()
    db.refresh(site)
    return site


@router.post('/bootstrap/henan')
def bootstrap_henan_sites(db: Session = Depends(get_db_session), _: User = Depends(require_admin)):
    created: list[str] = []
    skipped: list[str] = []

    for preset in HENAN_SEED_SITES:
        existing = db.query(Site).filter(Site.base_url == preset['base_url']).first()
        if existing:
            skipped.append(preset['name'])
            continue
        site = Site(**preset)
        db.add(site)
        created.append(preset['name'])

    db.commit()
    return {
        'created_count': len(created),
        'skipped_count': len(skipped),
        'created': created,
        'skipped': skipped,
    }


@router.put('/{site_id}', response_model=SiteOut)
def update_site(
    site_id: int,
    payload: SiteUpdateRequest,
    db: Session = Depends(get_db_session),
    _: User = Depends(require_admin),
):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail='site not found')

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(site, key, value)

    db.add(site)
    db.commit()
    db.refresh(site)
    return site
