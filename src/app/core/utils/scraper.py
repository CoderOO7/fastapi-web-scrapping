import time
import requests
import base64

from typing import Annotated
from bs4 import BeautifulSoup
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends


from ...schemas.scrape import ScrapeRequestBody
from ...schemas.product import ProductCreate
from ...core.db.database import async_get_db
from ...crud.crud_product import crud_product
from ...core.logger import logging

logger = logging.getLogger(__name__)

redis_client = Redis(host="redis", port=6379)

class Scraper:
    BASE_URL = "https://dentalstall.com/shop"

    def __init__(self, options: ScrapeRequestBody, db: Annotated[AsyncSession, Depends(async_get_db)]):
        self.db = db
        self.page_limit = options.page_limit
        self.proxy = options.proxy
        self.products = []
        self.redis_client = redis_client

    async def scrape(self):
        page = 1
        while True:
            if self.page_limit and page > self.page_limit:
                break
            url = f"{self.BASE_URL}/page/{page}"
            try:
                response = self.get_response(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                await self.parse_page(soup)
                page += 1
            except Exception as e:
                raise ValueError(f"Error scraping {url}: {e}")
        logger.info(f"Scraped {len(self.products)} products")

    async def fetch_page(self, url: str, retries: int = 3, delay: int = 5):
        for attempt in range(retries):
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
                response = requests.get(url, headers=headers, proxies=proxies)
                response.raise_for_status()
                response.raise_for_status()  # Raise an error for HTTP error codes
                return response  # Return the page content if successful
            except requests.exceptions.HTTPError as http_err:
                # Handle specific HTTP errors (like 500, 503, etc.)
                if response.status_code in {500, 503}:
                    logger.error(f"Server error encountered: {http_err}. Retrying in {delay} seconds...")
                else:
                    raise ValueError(str(http_err))
            except requests.exceptions.RequestException as req_err:
                # Handle other network-related errors (like connection errors)
                logger.error(f"Network error encountered: {req_err}. Retrying in {delay} seconds...")

            time.sleep(delay)  # Wait before retrying

        # Raise an exception if all retries fail
        raise ValueError("Maximum retries exceeded. Unable to fetch page")

    def get_response(self, url: str):
        headers = {"User-Agent": "Mozilla/5.0"}
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        response = requests.get(url, headers=headers, proxies=proxies)
        response.raise_for_status()
        return response

    async def parse_page(self, soup: BeautifulSoup):
        products = soup.select(".product")
        for product in products:
            title = product.select_one(".woo-loop-product__title").text.strip().replace('...', '')
            price = float(product.select_one(".woocommerce-Price-amount").text.strip().replace('₹', ''))
            product_url = product.select_one(".woo-loop-product__title > a")["href"]
            cached_key_title = product_url.split('/product/')[1]

            # if cache miss happen
            if not self.is_cached(cached_key_title, price):

                # if title.endswith("..."):
                #     title = self.get_full_title(product_url)

                image_url = product.select_one(".attachment-woocommerce_thumbnail")["data-lazy-src"]
                bas64_img = self.getBase64ImageFromUrl(image_url)

                product = ProductCreate(title=title, price=price, image=bas64_img)
                # save in db
                created_product = await crud_product.create(db=self.db, object=product)
                self.products.append(created_product)

                # save in in-memory db
                self.cache_product(cached_key_title, price)

    def get_full_title(self, product_url: str) -> str:
        try:
            response = self.get_response(product_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            full_title = soup.select_one(".product_title").text.strip()
            return full_title
        except requests.RequestException as e:
            raise ValueError(f"Error fetching full title from {product_url}: {e}")

    def getBase64ImageFromUrl(self, image_url: str):
        response = requests.get(image_url)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode('utf-8')  # Encode to Base64
        else:
            raise ValueError(f"Failed to retrieve image from URL: {response.status_code}")

    def is_cached(self, title: str, price: float) -> bool:
        cached_price =  self.redis_client.get(f"PRODUCTS_{title}")
        return cached_price is not None and float(cached_price) == price

    def cache_product(self, title: str, price: float):
        self.redis_client.set(f"PRODUCTS_{title}", price)