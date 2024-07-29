from fastapi import APIRouter

from .scrape import router as scrape_router

router = APIRouter(prefix="/v1")

router.include_router(scrape_router)
