"""
FastAPI entry point.

Routes:
  POST /chat              Main chat endpoint
  GET  /products          Browse the catalog
  GET  /products/{id}     Single product
  POST /cart/add          Programmatic cart add (e.g. from product card click)
  POST /cart/remove       Remove from cart
  GET  /cart              Inspect current cart
  GET  /health            Liveness check

Run locally:
    uvicorn main:app --reload --port 8000
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.catalog import catalog
from app.chatbot import engine
from app.models import ChatRequest, ChatResponse
from app.sessions import store

app = FastAPI(
    title="Retail AI Chatbot",
    description="An e-commerce conversational assistant with intent classification, "
                "product search, cart management, and order tracking.",
    version="1.0.0",
)

# CORS — open in dev. Tighten for production by setting allow_origins explicitly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Schemas for non-chat endpoints ────────────────────────
class CartAddRequest(BaseModel):
    session_id: str
    product_id: str
    quantity: int = 1
    size: str | None = None


class CartRemoveRequest(BaseModel):
    session_id: str
    product_id: str


# ─── Endpoints ─────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "products": len(catalog.all())}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    session = store.get_or_create(req.session_id)
    return engine.respond(req.message, session)


@app.get("/products")
def list_products(
    category: str | None = None,
    color: str | None = None,
    price_max: int | None = None,
    limit: int = 12,
):
    return catalog.search(
        categories=[category] if category else None,
        colors=[color] if color else None,
        price_max=price_max,
        limit=limit,
    )


@app.get("/products/{product_id}")
def get_product(product_id: str):
    p = catalog.get(product_id)
    if not p:
        raise HTTPException(404, f"Product {product_id} not found")
    return p


@app.get("/cart")
def view_cart(session_id: str):
    session = store.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return {
        "items":    session.cart,
        "subtotal": session.cart_subtotal(),
    }


@app.post("/cart/add")
def cart_add(req: CartAddRequest):
    session = store.get_or_create(req.session_id)
    product = catalog.get(req.product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    session.add_to_cart(product, quantity=req.quantity, size=req.size)
    return {"ok": True, "cart_size": len(session.cart), "subtotal": session.cart_subtotal()}


@app.post("/cart/remove")
def cart_remove(req: CartRemoveRequest):
    session = store.get(req.session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    removed = session.remove_from_cart(req.product_id)
    return {"ok": removed, "cart_size": len(session.cart), "subtotal": session.cart_subtotal()}


@app.get("/")
def root():
    return {
        "name": "Retail AI Chatbot",
        "version": app.version,
        "docs": "/docs",
        "chat_endpoint": "POST /chat with { message, session_id? }",
    }
