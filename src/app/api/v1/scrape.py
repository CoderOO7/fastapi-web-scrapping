from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...schemas.scrape import ScrapeRequestBody
from ...core.logger import logging
from ...core.utils.scraper import Scraper
from ...core.exceptions.http_exceptions import CustomException
from ...core.db.database import async_get_db


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scrape", tags=["scrape"])


@router.post("")
async def scrape(data: ScrapeRequestBody, db: Annotated[AsyncSession, Depends(async_get_db)]):
    logger.info('Executing scrape post route')
    if data.page_limit < 1:
        raise CustomException(status_code=400,  detail="Page limit should be greater than or equal to 1")
    try:
        scraper = Scraper(data, db)
        await scraper.scrape()
        return {"message": f"Scraped {len(scraper.products)} products"}
    except Exception as ex:
        raise CustomException(status_code=500, detail=f"{ex}")



