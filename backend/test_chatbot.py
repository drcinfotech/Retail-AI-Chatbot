"""
Smoke tests for the chatbot — run from the backend directory:
    python test_chatbot.py

Verifies:
  * Intent classifier returns the expected intent for representative messages
  * Entity extraction (price ceilings, order IDs) works
  * Product search returns relevant items
  * Cart operations persist within a session
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.chatbot import engine
from app.intents import classify
from app.catalog import catalog
from app.sessions import store


def assert_eq(actual, expected, label):
    status = "✓" if actual == expected else "✗"
    print(f"  {status} {label}: got {actual!r}, expected {expected!r}")
    return actual == expected


def main():
    failed = 0
    total = 0

    print("\n[1] Intent classification")
    cases = [
        ("hi there",                                  "greeting"),
        ("find me a gift for my sister",              "gift_help"),
        ("add the first one to my cart",              "add_to_cart"),
        ("show my cart",                              "view_cart"),
        ("any coupons available?",                    "discount_promo"),
        ("track my order TRK-8829145",                "track_order"),
        ("where can I return something",              "return_item"),
        ("I want to talk to a human",                 "talk_to_human"),
        ("do you have headphones under 30000?",       "product_search"),
        ("recommend something for my mom",            "recommend"),
        ("thanks bye",                                "goodbye"),
        ("how much is shipping?",                     "shipping_info"),
        ("what size should I order?",                 "size_help"),
    ]
    for msg, expected in cases:
        c = classify(msg)
        total += 1
        if not assert_eq(c.intent, expected, msg):
            failed += 1

    print("\n[2] Entity extraction")
    c = classify("find me a gift for her under ₹5000")
    total += 1
    if not assert_eq(c.entities["price_ceiling"], 5000, "price ceiling"): failed += 1
    total += 1
    if not assert_eq(c.entities["gender"], "women", "gender (women)"): failed += 1
    total += 1
    if not assert_eq("gift" in c.entities["tags"], True, "gift tag"): failed += 1

    c = classify("track order TRK-8829145")
    total += 1
    if not assert_eq(c.entities["order_id"], "TRK-8829145", "order id"): failed += 1

    print("\n[3] Product search")
    results = catalog.search(tags=["gift"], price_max=5000, limit=3)
    total += 1
    if not assert_eq(len(results) > 0, True, "gift items under 5000 returned"): failed += 1
    total += 1
    all_in_budget = all(p["price"] <= 5000 for p in results)
    if not assert_eq(all_in_budget, True, "all results within price ceiling"): failed += 1

    print("\n[4] Cart persistence across turns")
    session = store.get_or_create(None)
    engine.respond("find me a minimalist gift", session)
    engine.respond("add it to my cart", session)
    total += 1
    if not assert_eq(len(session.cart), 1, "cart has 1 item after add"): failed += 1
    total += 1
    if not assert_eq(session.cart_subtotal() > 0, True, "subtotal computed"): failed += 1

    print(f"\nResult: {total - failed}/{total} passed")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
