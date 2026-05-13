"""
Intent classifier for the retail chatbot.

Uses a hybrid pattern + keyword-scoring approach. No external ML
dependencies — works deterministically and is easy to extend.

How it works:
  1. Each intent has a list of regex patterns (high-confidence hits)
     and a list of keywords (cumulative scoring).
  2. The classifier scans the user's lowercased message against every
     intent and returns the top scorer (or `unknown` if no score crosses
     the threshold).
  3. Entities (prices, categories, colors, order IDs, etc.) are
     extracted separately and returned alongside the intent.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


# ─── Intent definitions ────────────────────────────────────
@dataclass
class IntentSpec:
    name: str
    patterns: list[str] = field(default_factory=list)   # high-confidence regex hits
    keywords: list[str] = field(default_factory=list)   # scoring tokens


INTENTS: list[IntentSpec] = [
    IntentSpec(
        "greeting",
        patterns=[r"^\s*(hi|hello|hey|hola|namaste|yo|good (morning|afternoon|evening))\b"],
        keywords=["hi", "hello", "hey", "hola", "namaste", "greetings"],
    ),
    IntentSpec(
        "goodbye",
        patterns=[r"\b(bye|goodbye|see ya|see you|catch you later|thanks bye|cya)\b"],
        keywords=["bye", "goodbye", "later", "thanks", "thank"],
    ),
    IntentSpec(
        "track_order",
        patterns=[
            r"\btrack\b.*\border\b",
            r"\b(where('?s)?|status of)\s+(my\s+)?(order|package|delivery|shipment)\b",
            r"\border\s*#?\s*[A-Z]{2,4}-\d{3,}",
            r"\b(when|how soon).+(arrive|deliver|reach)\b",
        ],
        keywords=["track", "tracking", "order", "package", "delivery", "shipment", "arrive", "deliver"],
    ),
    IntentSpec(
        "return_item",
        patterns=[
            r"\b(return|refund|send back|exchange)\b",
            r"\bdon'?t (like|want)\b",
            r"\b(return policy|refund policy)\b",
        ],
        keywords=["return", "refund", "exchange", "policy"],
    ),
    IntentSpec(
        "add_to_cart",
        patterns=[
            r"\badd\b.+\bto\s+(?:my\s+)?(cart|basket|bag)\b",
            r"\b(put|drop)\s+.+(?:in|into)\s+(?:my\s+)?(cart|basket|bag)\b",
            r"\b(i'?ll take|i want|buy|order|grab)\s+(it|that|this|the\s+\w+)\b",
            r"\badd\s+(it|that|this|the\s+(first|second|third|earrings|scarf|shirt|jeans|sneakers|headphones|watch|bag|dress|sweater|bottle|robe))\b",
        ],
        keywords=["add", "buy", "take", "purchase", "grab"],
    ),
    IntentSpec(
        "view_cart",
        patterns=[
            r"\b(show|view|check|see|what(?:'?s| is) in)\s+(my\s+)?(cart|basket|bag)\b",
            r"\bmy\s+(cart|basket|bag)\b",
            r"^\s*cart\s*$",
        ],
        keywords=["cart", "basket", "checkout"],
    ),
    IntentSpec(
        "checkout",
        patterns=[
            r"\b(check\s*out|pay\s+now|place\s+order|buy\s+now|complete\s+(?:my\s+)?order)\b",
        ],
        keywords=["checkout", "pay", "purchase", "complete"],
    ),
    IntentSpec(
        "discount_promo",
        patterns=[
            r"\b(coupons?|promo\s*codes?|discounts?|sales?|offers?|deals?)\b",
            r"\bany.+(off|discount|sale)\b",
            r"\bvouchers?\b",
        ],
        keywords=["coupon", "discount", "sale", "promo", "offer", "deal", "off", "voucher"],
    ),
    IntentSpec(
        "shipping_info",
        patterns=[
            r"\b(shipping|delivery)\s+(cost|fee|charge|time|duration)\b",
            r"\b(how long|how much).+(ship|deliver)\b",
            r"\bfree shipping\b",
        ],
        keywords=["shipping", "delivery", "ship", "cost", "fee"],
    ),
    IntentSpec(
        "size_help",
        patterns=[
            r"\b(size chart|size guide|what size|which size|fit guide)\b",
            r"\b(small|medium|large)\s+(or|vs)\s+(small|medium|large)\b",
        ],
        keywords=["size", "fit", "small", "medium", "large", "chart", "guide"],
    ),
    IntentSpec(
        "talk_to_human",
        patterns=[
            r"\b(human|agent|representative|real person|talk to (someone|support))\b",
            r"\b(speak|connect)\s+to\s+(an?\s+)?(agent|person|human)\b",
        ],
        keywords=["human", "agent", "representative", "person", "support"],
    ),
    IntentSpec(
        "product_search",
        patterns=[
            r"\b(find|search|look(ing)? for|show me|i need|i want|do you have)\b",
            r"\bin\s+stock\b",
            r"\b(under|less than|below)\s*₹?\s*\d+",
        ],
        keywords=["find", "search", "looking", "show", "need", "want", "browse"],
    ),
    IntentSpec(
        "gift_help",
        patterns=[
            r"\b(gift|present|birthday|anniversary|christmas|diwali|housewarming|wedding)\b",
            r"\bsomething for (my|her|him|them)\b",
            r"\b(gift|present)\s+(for|idea)\b",
        ],
        keywords=["gift", "present", "birthday", "anniversary", "diwali", "christmas"],
    ),
    IntentSpec(
        "recommend",
        patterns=[
            r"\b(recommend|suggest|what do you (suggest|recommend|think))\b",
            r"\bwhat'?s good\b",
            r"\bbest\s+\w+\b",
        ],
        keywords=["recommend", "suggest", "best", "popular", "trending"],
    ),
    IntentSpec(
        "thanks",
        patterns=[r"^\s*(thanks|thank you|thx|ty|appreciate it)\b"],
        keywords=["thanks", "thank", "appreciate"],
    ),
]


# ─── Entity extractors ─────────────────────────────────────
CATEGORIES = {
    "clothing":    ["clothing", "clothes", "apparel", "outfit"],
    "shirts":      ["shirt", "shirts", "button-down", "button down"],
    "jeans":       ["jeans", "denim"],
    "sweaters":    ["sweater", "sweaters", "jumper", "pullover"],
    "dresses":     ["dress", "dresses", "frock", "gown"],
    "shoes":       ["shoes", "sneakers", "trainers", "footwear"],
    "running":     ["running shoes", "runners"],
    "bags":        ["bag", "bags", "tote", "totes", "handbag", "purse", "backpack"],
    "jewelry":     ["jewelry", "jewellery", "earring", "earrings", "necklace", "ring"],
    "accessories": ["accessory", "accessories", "belt", "wallet", "hat", "scarf", "sunglasses"],
    "electronics": ["electronics", "gadget", "tech"],
    "audio":       ["headphones", "earbuds", "speaker", "audio"],
    "wearables":   ["watch", "smartwatch", "fitness tracker", "fitness watch"],
    "home":        ["home", "decor", "decoration"],
    "kitchen":     ["kitchen", "cookware", "skillet", "pan", "pot"],
    "beauty":      ["beauty", "skincare", "fragrance", "perfume", "serum", "body wash"],
    "fitness":     ["fitness", "gym", "workout", "yoga"],
    "coffee":      ["coffee", "espresso", "beans"],
    "stationery":  ["stationery", "pen", "pencil", "notebook"],
}

COLORS = [
    "black", "white", "grey", "gray", "navy", "blue", "red", "green", "olive",
    "tan", "brown", "cream", "ivory", "gold", "silver", "rose", "pink",
    "yellow", "orange", "purple", "indigo", "sage", "stone", "charcoal", "rust",
]

GENDERS = {
    "women": ["women", "woman", "her", "she", "girl", "ladies"],
    "men":   ["men", "man", "him", "he", "boy", "gents"],
    "unisex": ["unisex", "everyone"],
}


def extract_price_ceiling(text: str) -> Optional[int]:
    """Find a price ceiling phrase like 'under 5000', 'below ₹3K', 'less than 10k'."""
    text = text.lower()
    # patterns: under <num>k|<num>
    m = re.search(r"(?:under|below|less than|cheaper than|max(?:imum)?)\s*₹?\s*(\d+)\s*(k|thousand)?", text)
    if m:
        n = int(m.group(1))
        if m.group(2):
            n *= 1000
        return n
    return None


def extract_categories(text: str) -> list[str]:
    text = text.lower()
    found = []
    for cat, words in CATEGORIES.items():
        if any(w in text for w in words):
            found.append(cat)
    return found


def extract_colors(text: str) -> list[str]:
    text = text.lower()
    return [c for c in COLORS if re.search(rf"\b{c}\b", text)]


def extract_gender(text: str) -> Optional[str]:
    text = text.lower()
    for g, words in GENDERS.items():
        if any(re.search(rf"\b{w}\b", text) for w in words):
            return g
    return None


def extract_tags(text: str) -> list[str]:
    """Tags that aren't strict categories — e.g. 'minimalist', 'gift', 'wedding'."""
    text = text.lower()
    candidate = ["minimalist", "gift", "luxury", "casual", "summer", "winter",
                 "wedding", "everyday", "work", "travel", "sustainable",
                 "vintage", "modern", "classic"]
    return [t for t in candidate if t in text]


def extract_order_id(text: str) -> Optional[str]:
    """Pull an order id like TRK-8829145 or LU-44219."""
    m = re.search(r"\b([A-Z]{2,4}-?\d{4,})\b", text.upper())
    return m.group(1) if m else None


# ─── Classifier ────────────────────────────────────────────
@dataclass
class Classification:
    intent: str
    confidence: float
    entities: dict


def classify(text: str) -> Classification:
    """Return (intent, confidence, entities) for the user's message."""
    raw = text
    text_lc = text.lower().strip()

    scores: dict[str, float] = {}

    for spec in INTENTS:
        score = 0.0
        # Regex patterns are worth more (high precision signal)
        for p in spec.patterns:
            if re.search(p, text_lc, re.IGNORECASE):
                score += 2.0
        # Keywords accumulate
        for kw in spec.keywords:
            if re.search(rf"\b{re.escape(kw)}\b", text_lc):
                score += 0.6
        if score > 0:
            scores[spec.name] = score

    if not scores:
        intent, conf = "unknown", 0.0
    else:
        intent = max(scores, key=scores.get)
        # Confidence is the top score divided by the second-best, capped 0–1.
        top = scores[intent]
        rest = sorted(scores.values(), reverse=True)[1] if len(scores) > 1 else 0.1
        conf = min(1.0, top / (top + rest))

    entities = {
        "categories":     extract_categories(raw),
        "colors":         extract_colors(raw),
        "gender":         extract_gender(raw),
        "tags":           extract_tags(raw),
        "price_ceiling":  extract_price_ceiling(raw),
        "order_id":       extract_order_id(raw),
    }

    return Classification(intent=intent, confidence=round(conf, 2), entities=entities)
