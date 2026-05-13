"""
The chatbot engine.

Given a user message and a session, produces a response made up of one or
more rich blocks (text, products, cart, order, promo).

This is intentionally rule-based and deterministic — easy to read, easy to
extend, and runs without an API key. To plug in an LLM later, swap out the
`respond` method to call your model and translate its output into Blocks.
"""
from __future__ import annotations

from typing import Optional

from .catalog import catalog
from .intents import Classification, classify
from .sessions import Session


# ─── Helpers ───────────────────────────────────────────────
SHIPPING_FLAT = 49           # Flat shipping fee in INR
FREE_SHIPPING_THRESHOLD = 1500


def _build_text(content: str) -> dict:
    return {"type": "text", "content": content}


def _build_products(items: list[dict], title: Optional[str] = None) -> dict:
    return {"type": "products", "title": title, "items": items}


def _build_cart(session: Session) -> dict:
    subtotal = session.cart_subtotal()
    shipping = 0 if subtotal >= FREE_SHIPPING_THRESHOLD else SHIPPING_FLAT
    if not session.cart:
        shipping = 0
    return {
        "type": "cart",
        "items": session.cart,
        "subtotal": subtotal,
        "shipping": shipping,
        "total":    subtotal + shipping,
    }


def _build_order(order_id: str) -> dict:
    """Return a deterministic fake order for the demo."""
    return {
        "type": "order",
        "order": {
            "order_id":    order_id,
            "status":      "In transit",
            "eta":         "Thu, Dec 04 by 6 PM",
            "items_count": 3,
            "total":       4870,
            "events": [
                {"label": "Ordered",          "date": "Mon, Dec 01", "done": True},
                {"label": "Packed",           "date": "Tue, Dec 02", "done": True},
                {"label": "Shipped",          "date": "Wed, Dec 03", "done": True, "current": True},
                {"label": "Out for delivery", "date": "Thu, Dec 04", "done": False},
                {"label": "Delivered",        "date": "Thu, Dec 04", "done": False},
            ],
        },
    }


def _build_promo(code: str, description: str, discount_pct: int) -> dict:
    return {
        "type": "promo",
        "code": code,
        "description": description,
        "discount_pct": discount_pct,
    }


# ─── Intent handlers ───────────────────────────────────────
def _handle_greeting(session: Session) -> tuple[list[dict], list[str]]:
    blocks = [_build_text(
        "Hi, I'm Lume — your shopping assistant. I can help you find products, "
        "track orders, manage your cart, or just talk through what you need. "
        "What brings you in today?"
    )]
    suggestions = ["Find a gift", "Track my order", "Show trending items", "Return an item"]
    return blocks, suggestions


def _handle_search(c: Classification, session: Session) -> tuple[list[dict], list[str]]:
    e = c.entities
    items = catalog.search(
        categories    = e["categories"] or None,
        colors        = e["colors"]     or None,
        tags          = e["tags"]       or None,
        gender        = e["gender"],
        price_max     = e["price_ceiling"],
        limit         = 3,
    )

    if not items:
        items = catalog.random_sample(3)
        intro = "I didn't find an exact match, but here are a few customer favorites you might like:"
    else:
        bits = []
        if e["categories"]: bits.append(", ".join(e["categories"]))
        if e["colors"]:     bits.append(f"in {', '.join(e['colors'])}")
        if e["price_ceiling"]: bits.append(f"under ₹{e['price_ceiling']:,}")
        descriptor = " ".join(bits) or "what you described"
        intro = f"Found these for {descriptor} — sorted by rating and fit to your filters:"

    session.last_products_shown = [p["id"] for p in items]

    blocks = [_build_text(intro), _build_products(items)]
    suggestions = ["Show more options", "Filter by price", "Add the first to cart", "View my cart"]
    return blocks, suggestions


def _handle_gift(c: Classification, session: Session) -> tuple[list[dict], list[str]]:
    e = c.entities
    items = catalog.search(
        tags=["gift"] + (e["tags"] or []),
        categories=e["categories"] or None,
        gender=e["gender"],
        price_max=e["price_ceiling"],
        limit=3,
    )
    if not items:
        items = catalog.search(tags=["gift"], limit=3)

    session.last_products_shown = [p["id"] for p in items]
    blocks = [
        _build_text("Gifting is one of my favorite things. A few thoughtful picks from brands people love:"),
        _build_products(items),
    ]
    return blocks, ["Wrap as a gift", "Show more gift ideas", "Under ₹2,000", "Add the first one"]


def _handle_recommend(c: Classification, session: Session) -> tuple[list[dict], list[str]]:
    e = c.entities
    if e["categories"]:
        items = catalog.popular(category=e["categories"][0], limit=3)
    else:
        items = catalog.popular(limit=3)
    session.last_products_shown = [p["id"] for p in items]
    blocks = [
        _build_text("These are trending this week — high ratings and consistently strong reviews:"),
        _build_products(items),
    ]
    return blocks, ["Tell me more about the first", "Add to cart", "Show fresh arrivals", "Filter by under ₹5K"]


def _handle_track_order(c: Classification, _session: Session) -> tuple[list[dict], list[str]]:
    order_id = c.entities["order_id"] or "TRK-8829145"
    blocks = [
        _build_text(f"Found order {order_id}. Here's where it is right now:"),
        _build_order(order_id),
        _build_text("Want me to switch to a different delivery window, or notify you 30 minutes before arrival?"),
    ]
    return blocks, ["Change delivery window", "Notify before arrival", "Cancel order", "Talk to a human"]


def _handle_return(_c: Classification, _session: Session) -> tuple[list[dict], list[str]]:
    blocks = [_build_text(
        "Returns are simple — you have 30 days from delivery, and the first return per order is free. "
        "Tell me the order number or product name and I'll start the return for you. "
        "Refunds typically post to your original payment within 5–7 business days."
    )]
    return blocks, ["Start a return", "Return policy", "Talk to a human", "Track refund"]


def _handle_view_cart(session: Session) -> tuple[list[dict], list[str]]:
    if not session.cart:
        blocks = [
            _build_text(
                "Your cart is empty right now. Tell me what you're after and I'll line up some options."
            )
        ]
        return blocks, ["Show trending items", "Find a gift", "Browse new arrivals"]
    blocks = [
        _build_text(f"You've got {len(session.cart)} item(s) in your cart:"),
        _build_cart(session),
    ]
    return blocks, ["Checkout", "Apply a coupon", "Continue shopping", "Empty cart"]


def _handle_add_to_cart(session: Session) -> tuple[list[dict], list[str]]:
    """Add the first product the user was just shown."""
    if not session.last_products_shown:
        return ([_build_text(
            "Sure — which item would you like me to add? Tell me a product name or share a link."
        )], ["Show trending items", "Find a gift"])

    product = catalog.get(session.last_products_shown[0])
    if not product:
        return ([_build_text("I couldn't find that item again — could you describe it once more?")], [])

    session.add_to_cart(product)
    blocks = [
        _build_text(f"Added **{product['name']}** by {product['brand']} to your cart."),
        _build_cart(session),
    ]
    return blocks, ["Checkout", "Apply a coupon", "Keep shopping", "Empty cart"]


def _handle_checkout(session: Session) -> tuple[list[dict], list[str]]:
    if not session.cart:
        return ([_build_text(
            "Your cart is empty — let me know what you'd like to add and we'll go from there."
        )], ["Show trending items", "Find a gift"])
    total = session.cart_subtotal()
    blocks = [
        _build_text(
            f"Ready to check out. Total comes to ₹{total:,} "
            f"({len(session.cart)} item(s){'  · free shipping' if total >= FREE_SHIPPING_THRESHOLD else ''}). "
            "I'll use your saved address and the card ending 4421 unless you want to change something."
        ),
        _build_cart(session),
    ]
    return blocks, ["Place order", "Change address", "Change payment", "Apply a coupon"]


def _handle_discount(_session: Session) -> tuple[list[dict], list[str]]:
    blocks = [
        _build_text("Two active offers right now — both stack with any single item in your cart:"),
        _build_promo("WELCOME10",  "10% off your first order (no minimum)",                  10),
        _build_promo("HOLIDAY500", "Flat ₹500 off when you spend ₹3,000 or more this week.", 0),
        _build_text("Want me to apply WELCOME10 to your current cart?"),
    ]
    return blocks, ["Apply WELCOME10", "Apply HOLIDAY500", "Show me eligible items", "Skip"]


def _handle_shipping(_session: Session) -> tuple[list[dict], list[str]]:
    blocks = [_build_text(
        "Standard shipping is ₹49 and arrives in 3–5 business days. "
        "Free over ₹1,500. Express (next-day in most metros) is ₹199. "
        "International shipping varies — share a destination and I'll quote it."
    )]
    return blocks, ["Free shipping items", "Express delivery", "International rates"]


def _handle_size_help(_session: Session) -> tuple[list[dict], list[str]]:
    blocks = [_build_text(
        "Most of our brands run true to size, but a few quirks worth knowing: "
        "Marisol Studio runs slightly small (size up if you're between), Threadline runs true, "
        "and Soleva sneakers are 1/2 size large — order down. Share the product and "
        "your usual size, and I'll give you a confident pick."
    )]
    return blocks, ["Marisol Studio sizing", "Threadline sizing", "Soleva sizing", "Show size chart"]


def _handle_talk_to_human(_session: Session) -> tuple[list[dict], list[str]]:
    blocks = [_build_text(
        "Of course. I'm connecting you to an agent — typical wait time right now is about 2 minutes. "
        "If you'd rather not wait, I can have someone email you within the hour. Which works better?"
    )]
    return blocks, ["Wait for chat", "Email me instead", "Schedule a callback"]


def _handle_thanks(_session: Session) -> tuple[list[dict], list[str]]:
    return ([_build_text("Anytime. I'm here whenever you need.")],
            ["Show trending items", "Track my order", "Find a gift"])


def _handle_goodbye(_session: Session) -> tuple[list[dict], list[str]]:
    return ([_build_text("Take care — and your cart will be here whenever you're back.")], [])


def _handle_unknown(_c: Classification, session: Session) -> tuple[list[dict], list[str]]:
    items = catalog.popular(limit=3)
    session.last_products_shown = [p["id"] for p in items]
    blocks = [
        _build_text(
            "I didn't quite catch that. I'm best at finding products, tracking orders, "
            "and helping with returns. While you think — here are this week's most loved items:"
        ),
        _build_products(items),
    ]
    return blocks, ["Find a gift", "Track my order", "Return policy", "Talk to a human"]


# ─── Engine ────────────────────────────────────────────────
class ChatbotEngine:
    """Wraps the classifier + handlers behind a single `respond` method."""

    def respond(self, message: str, session: Session) -> dict:
        c = classify(message)
        session.last_intent = c.intent
        session.history.append({"role": "user", "text": message})

        handler_map = {
            "greeting":         lambda: _handle_greeting(session),
            "goodbye":          lambda: _handle_goodbye(session),
            "thanks":           lambda: _handle_thanks(session),
            "product_search":   lambda: _handle_search(c, session),
            "gift_help":        lambda: _handle_gift(c, session),
            "recommend":        lambda: _handle_recommend(c, session),
            "track_order":      lambda: _handle_track_order(c, session),
            "return_item":      lambda: _handle_return(c, session),
            "view_cart":        lambda: _handle_view_cart(session),
            "add_to_cart":      lambda: _handle_add_to_cart(session),
            "checkout":         lambda: _handle_checkout(session),
            "discount_promo":   lambda: _handle_discount(session),
            "shipping_info":    lambda: _handle_shipping(session),
            "size_help":        lambda: _handle_size_help(session),
            "talk_to_human":    lambda: _handle_talk_to_human(session),
        }

        handler = handler_map.get(c.intent, lambda: _handle_unknown(c, session))
        blocks, suggestions = handler()

        # Record a flattened text version for history
        bot_text = " | ".join(b["content"] for b in blocks if b.get("type") == "text")
        session.history.append({"role": "bot", "text": bot_text})

        return {
            "session_id": session.session_id,
            "intent":     c.intent,
            "confidence": c.confidence,
            "blocks":     blocks,
            "suggestions": suggestions,
        }


engine = ChatbotEngine()
