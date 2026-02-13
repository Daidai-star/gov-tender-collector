from fastapi import APIRouter

from app.api.v1.endpoints import auth, crawl, notices, sites, tasks

api_router = APIRouter()
api_router.include_router(auth.router, prefix='/auth', tags=['auth'])
api_router.include_router(crawl.router, prefix='/crawl', tags=['crawl'])
api_router.include_router(notices.router, prefix='/notices', tags=['notices'])
api_router.include_router(sites.router, prefix='/sites', tags=['sites'])
api_router.include_router(tasks.router, prefix='/tasks', tags=['tasks'])
