from dataclasses import dataclass


@dataclass(slots=True)
class Article:
    id: int
    category_id: int
    name: str
    price: float
    stock: float = 0
    purchase_price: float = 0
    article_type: str = "SINGLE"
    stock_unit: str = "Stück"
    