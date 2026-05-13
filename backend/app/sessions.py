"""
Lightweight in-memory session store.

For production, swap the dict for Redis or a real DB. The interface is the same.
"""
from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class Session:
    session_id: str
    cart: list[dict] = field(default_factory=list)   # [{product_id, name, brand, price, image, quantity, size?}]
    last_intent: str = ""
    last_products_shown: list[str] = field(default_factory=list)
    history: list[dict] = field(default_factory=list)  # [{role, text}]

    # ── Cart operations ───────────────────────────────────
    def add_to_cart(self, product: dict, quantity: int = 1, size: str | None = None) -> None:
        for item in self.cart:
            if item["product_id"] == product["id"] and item.get("size") == size:
                item["quantity"] += quantity
                return
        self.cart.append({
            "product_id": product["id"],
            "name":       product["name"],
            "brand":      product["brand"],
            "price":      product["price"],
            "image":      product["image"],
            "quantity":   quantity,
            "size":       size,
        })

    def remove_from_cart(self, product_id: str) -> bool:
        before = len(self.cart)
        self.cart = [i for i in self.cart if i["product_id"] != product_id]
        return len(self.cart) < before

    def clear_cart(self) -> None:
        self.cart.clear()

    def cart_subtotal(self) -> int:
        return sum(i["price"] * i["quantity"] for i in self.cart)


class SessionStore:
    """Thread-safe in-memory dictionary of sessions, keyed by session_id."""

    def __init__(self):
        self._sessions: dict[str, Session] = {}
        self._lock = Lock()

    def get_or_create(self, session_id: str | None) -> Session:
        with self._lock:
            if session_id and session_id in self._sessions:
                return self._sessions[session_id]
            new_id = session_id or secrets.token_urlsafe(12)
            session = Session(session_id=new_id)
            self._sessions[new_id] = session
            return session

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)


# Singleton
store = SessionStore()
