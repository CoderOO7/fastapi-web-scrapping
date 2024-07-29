from fastcrud import FastCRUD

from ..models.product import Product
from ..schemas.product import ProductCreate, ProductUpdateInternal, ProductDelete, ProductUpdate

CRUDProduct = FastCRUD[Product, ProductCreate, ProductUpdate, ProductUpdateInternal, ProductDelete]
crud_product = CRUDProduct(Product)
