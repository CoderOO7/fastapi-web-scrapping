from pydantic import BaseModel
from typing import Optional


class ScrapeRequestBody(BaseModel):
    page_limit: Optional[int] = None
    proxy: Optional[str] = None
