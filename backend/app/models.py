"""
Pydantic models for the chatbot API.
These define the JSON shape of requests and responses.
"""
from __future__ import annotations

from typing import Optional, Literal
from pydantic import BaseModel, Field


# ─── Request ───────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    session_id: Optional[str] = None


# ─── Response building blocks ──────────────────────────────
class Product(BaseModel):
    id: str
    name: str
    brand: str
    category: str
    subcategory: str
    price: int
    currency: str
    color: str
    sizes: list[str]
    rating: float
    reviews: int
    stock: int
    image: str
    tags: list[str]
    description: str
    gender: str


class CartItem(BaseModel):
    product_id: str
    name: str
    brand: str
    price: int
    quantity: int
    image: str
    size: Optional[str] = None


class OrderEvent(BaseModel):
    label: str
    date: str
    done: bool
    current: bool = False


class Order(BaseModel):
    order_id: str
    status: str
    eta: str
    items_count: int
    total: int
    events: list[OrderEvent]


# ─── Rich message blocks the bot can return ────────────────
class TextBlock(BaseModel):
    type: Literal["text"] = "text"
    content: str


class ProductsBlock(BaseModel):
    type: Literal["products"] = "products"
    title: Optional[str] = None
    items: list[Product]


class CartBlock(BaseModel):
    type: Literal["cart"] = "cart"
    items: list[CartItem]
    subtotal: int
    shipping: int
    total: int


class OrderBlock(BaseModel):
    type: Literal["order"] = "order"
    order: Order


class PromoBlock(BaseModel):
    type: Literal["promo"] = "promo"
    code: str
    description: str
    discount_pct: int


MessageBlock = TextBlock | ProductsBlock | CartBlock | OrderBlock | PromoBlock


# ─── Response ──────────────────────────────────────────────
class ChatResponse(BaseModel):
    session_id: str
    intent: str
    confidence: float
    blocks: list[MessageBlock]
    suggestions: list[str] = []
