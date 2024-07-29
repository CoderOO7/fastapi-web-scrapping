from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from ..core.schemas import PersistentDeletion, TimestampSchema, UUIDSchema


class ProductBase(BaseModel):
    title: Annotated[str, Field(min_length=2, max_length=30, examples=["This is my product"])]
    price: Annotated[float, Field(examples=[123.12])]


class Product(TimestampSchema, ProductBase, UUIDSchema, PersistentDeletion):
    image: Annotated[
        str | None,
        Field(examples=[], default=None),
    ]


class ProductRead(BaseModel):
    id: int
    title: Annotated[str, Field(min_length=2, max_length=30, examples=["This is my product"])]
    price: Annotated[float, Field(examples=[123.12])]
    image: Annotated[
        str | None,
        Field(examples=[], default=None),
    ]
    created_at: datetime


class ProductCreate(ProductBase):
    image: Annotated[
        str | None,
        Field(examples=[], default=None),
    ]


class ProductUpdate(BaseModel):
    title: Annotated[str, Field(min_length=2, max_length=30, examples=["This is my product"])]
    price: Annotated[float, Field(examples=[123.12])]
    image: Annotated[
        str | None,
        Field(examples=[], default=None),
    ]


class ProductUpdateInternal(ProductUpdate):
    updated_at: datetime


class ProductDelete(BaseModel):
    pass